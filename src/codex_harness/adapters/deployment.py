from __future__ import annotations

import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock

from codex_harness.adapters.commands import run_process
from codex_harness.adapters.evaluator_migration import validate_controller, validate_manifest
from codex_harness.adapters.hooks import NativeHooks
from codex_harness.adapters.release_test_services import isolated_release_services
from codex_harness.application.releases import Releases
from codex_harness.application.workflow import Workflow
from codex_harness.domain.evaluator_migration import validate_approvals
from codex_harness.domain.model import canonical, digest, require, utcnow


@contextmanager
def incumbent_test_workspace(incumbent: str, candidate: str):
    """Keep incumbent tests/history while file-based fixtures inspect candidate source."""
    original, selected = Path(incumbent).resolve(), Path(candidate).resolve()
    require((original / '.git').is_dir(), 'Evaluator requires a native Git checkout')
    with tempfile.TemporaryDirectory(prefix='harness-incumbent-evaluator-') as directory:
        root = Path(directory) / 'evaluation'

        def ignore(path, names):
            excluded = {'__pycache__', '.pytest_cache', '.venv'}
            if Path(path).resolve() == original:
                excluded.add('src')
            return set(names) & excluded

        # INV-RELEASE-001: never rewrite either reviewed checkout or test bytes.
        # __file__-relative fixtures and imported code must describe one candidate.
        shutil.copytree(original, root, ignore=ignore)
        shutil.copytree(selected / 'src', root / 'src',
                        ignore=shutil.ignore_patterns('__pycache__'))
        yield root


class ReleaseRunner:
    """Host-side canary controller, independent of the candidate's Codex process."""

    def __init__(self, service, git, artifacts, auth: str, auto_merge: bool = True):
        self.service, self.git, self.artifacts = service, git, artifacts
        self.auth = Path(auth).resolve()
        self.auto_merge = auto_merge
        self.releases = Releases(service.store, service.org)

    def _check(self, argv: list[str], cwd: str | None = None, timeout: int = 300, env=None) -> dict:
        try:
            process = run_process(argv, cwd=cwd, timeout=timeout, env=env)
            receipt = self.artifacts.put(canonical({"argv": argv, "exit_code": process.returncode,
                                         "stdout": process.stdout, "stderr": process.stderr}), "canary")
            return {"passed": process.returncode == 0, "evidence": receipt["ref"]}
        except Exception as exc:
            receipt = self.artifacts.put(str(exc), "canary-failure")
            return {"passed": False, "evidence": receipt["ref"]}

    def run(self, release_id: str) -> dict:
        result = self._run(release_id)
        with self.service.store.transaction() as tx:
            item = tx.get("release_queue", release_id)
            if item:
                tx.put("release_queue", release_id, {**item, "status": result["status"], "result": result})
        return result

    def _run(self, release_id: str) -> dict:
        with self.service.store.transaction() as tx:
            release = tx.get("releases", release_id)
            active = tx.get("deployment", "active")
            image_record = tx.get("images", release_id)
        require(release is not None, "Release not found")
        validate_approvals(release, self.service.org)
        if 'migration' in release['policy']:
            validate_controller(release['policy'])
            validate_manifest(self.git.repository, release['policy'], release['candidate'])
        if release["status"] == "active":
            require(active and active["release_id"] == release_id, "Release is not the active deployment")
            return {"status": "active", "already_applied": True, "pointer": active}
        if release["status"] == "verified":
            require(image_record is not None, "Verified image receipt missing")
            return self._promote(release, active, image_record["image"])
        require(release["status"] == "reviewed", "Release not reviewed")
        candidate = release["candidate"]
        current_main = self.git._git("rev-parse", "HEAD")
        if current_main != candidate["base"]:
            require('migration' not in release['policy'],
                    'Migration source base is stale; fresh proposal and reviews required')
            request = Workflow(self.service.store, self.service.org).request_rebase(candidate["task_id"], current_main)
            return {"status": "rebasing", "task_id": request["message_id"]}
        inspected = self.git.inspect(candidate["revision"], candidate["base"])
        require(inspected["tree"] == candidate["tree"], "Candidate tree mismatch")
        evaluator_revision = release['policy'].get('evaluator_revision', candidate['base'])
        incumbent = self.git.review_workspace(evaluator_revision, "evaluator-" + release_id[:16])
        path = self.git.review_workspace(candidate["revision"], "canary-" + release_id[:16])
        # Fresh candidate venv; test definitions are taken from the incumbent commit.
        install = self._check(["uv", "sync", "--frozen"], path)
        python = Path(path) / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        with isolated_release_services(python, path, self.artifacts) as test_env:
            with incumbent_test_workspace(incumbent, path) as evaluator:
                incumbent_env = {**test_env, "PYTHONPATH": os.pathsep.join(
                    [str(evaluator / 'tests'), str(evaluator / 'src')])}
                tests = self._check([str(python), "-m", "pytest", str(evaluator / 'tests'),
                                     "-c", str(evaluator / 'pyproject.toml'),
                                     "--import-mode=importlib", "-q"],
                                    str(evaluator), timeout=900, env=incumbent_env)
            candidate_tests = self._check([str(python), "-m", "pytest", "-q"], path, timeout=900, env=test_env)
        tests = {"passed": tests["passed"] and candidate_tests["passed"],
                 "evidence": self.artifacts.put(canonical({"incumbent": tests, "candidate": candidate_tests,
                                                    "evaluator_revision": evaluator_revision,
                                                    "source_base": candidate['base'],
                                                    "candidate_revision": candidate['revision'],
                                                    "candidate_tree": candidate['tree'],
                                                    "policy_hash": release['policy_hash']}),
                                                "test-suites:" + release_id)["ref"]}
        if not install["passed"]:
            tests = install
        image = "codex-harness:candidate-" + candidate["revision"][:16]
        build = self._check(["docker", "build", "-t", image, path], timeout=600)
        if not build["passed"]:
            checks = {"tests": tests, "cli_start": build, "cli_file_task": build}
        else:
            inspected_image = run_process(["docker", "image", "inspect", image, "--format", "{{.Id}}"], timeout=30)
            require(inspected_image.returncode == 0, "Candidate image missing")
            image = inspected_image.stdout.strip()
            start = self._check(["docker", "run", "--rm", "--memory", "512m", "--cpus", "1",
                                 "--entrypoint", "codex", image, "--version"])
            task = self.file_canary(image)
            checks = {"tests": tests, "cli_start": start, "cli_file_task": task}
            with self.service.store.transaction() as tx:
                tx.put("images", release_id, {"id": release_id, "image": image, "revision": candidate["revision"]})
        if candidate.get("hook_id"):
            hook_checks = NativeHooks(self.service, self.git, self.artifacts).canary(candidate["hook_id"])
            checks.update({"hook_" + name: check for name, check in hook_checks.items()})
            hook = self.service.get_hook(candidate["hook_id"])
            self.service.record_canary(hook["id"], candidate["revision"], digest(hook["spec"]),
                                       {**{name: check["passed"] for name, check in hook_checks.items()},
                                        "cli_start": checks["cli_file_task"]["passed"]})
        verified = self.releases.verify(release_id, candidate["revision"], release["policy_hash"], checks)
        if verified["status"] != "verified":
            return {"status": "rejected", "checks": checks}
        return self._promote(verified, active, image)

    def _promote(self, release, active, image):
        validate_approvals(release, self.service.org)
        release_id, candidate, checks = release["id"], release["candidate"], release["checks"]
        if self.git.remote:
            self.git.publish(candidate, "Harness improvement " + candidate["revision"][:12],
                             "Implements a reviewed harness improvement.\n\n"
                             "Independent lead and conductor evidence, and incumbent-policy canary results:\n"
                             + canonical({"reviews": release["reviews"], "checks": checks}))
        if self.auto_merge:
            merged = self.git.merge(candidate)
        else:
            return {"status": "verified", "image": image, "checks": checks}
        pointer = self.releases.promote(release_id, (active or {}).get("release_id"))
        if candidate.get("hook_id"):
            self.service.activate(candidate["hook_id"])
        return {"status": "active", "pointer": pointer, "image": image, "merge": merged}

    def file_canary(self, image: str) -> dict:
        require(self.auth.is_file(), "Codex runtime authentication missing")
        with tempfile.TemporaryDirectory(prefix="harness-container-canary-") as directory:
            root = Path(directory)
            token = "HARNESS_CANARY_" + os.urandom(8).hex()
            (root / "input.txt").write_text(token, encoding="utf-8")
            schema = {"type": "object", "additionalProperties": False,
                      "properties": {"value": {"type": "string"}}, "required": ["value"]}
            (root / "schema.json").write_text(canonical(schema), encoding="utf-8")
            name = "harness-canary-" + os.urandom(6).hex()
            command = ["docker", "run", "--rm", "--name", name, "--memory", "768m", "--cpus", "1",
                       "--mount", f"type=bind,source={root},target=/canary",
                       "--mount", f"type=bind,source={self.auth},target=/root/.codex/auth.json,readonly",
                       "--entrypoint", "codex", image, "exec", "--ephemeral", "--skip-git-repo-check",
                       "--sandbox", "danger-full-access", "-c", 'approval_policy="never"',
                       "--output-schema", "/canary/schema.json", "--output-last-message", "/canary/result.json",
                       "-C", "/canary", "Read input.txt and write its exact contents to output.txt. "
                       "Return the input contents in value. Do not use network."]
            try:
                check = self._check(command, timeout=180)
                try:
                    answer = json.loads((root / "result.json").read_text("utf-8"))
                    valid = answer["value"] == token and (root / "output.txt").read_text("utf-8") == token
                except (OSError, ValueError, KeyError):
                    valid = False
                check["passed"] = check["passed"] and valid
                return check
            finally:
                # Docker client timeout alone does not terminate the daemon-owned container.
                run_process(["docker", "rm", "-f", name], timeout=30)

    def rollback_if_compatible(self, active: dict, reason: str) -> dict:
        # INV-RELEASE-001: a healthy old CLI does not prove that its writers
        # enforce tombstones. Unknown compatibility must not restore old writers.
        with self.service.store.transaction() as tx:
            current = tx.get('releases', active['release_id'])
            previous = tx.get('releases', (active.get('previous') or {}).get('release_id', ''))
        paths = ['src/codex_harness/adapters/store.py',
                     'src/codex_harness/adapters/record_references.py',
                     'src/codex_harness/adapters/artifacts.py',
                     'src/codex_harness/application/rlm.py']
        compatibility_error = None
        try:
            require(current is not None and previous is not None, 'Rollback source identity missing')
            revisions = [r['candidate']['revision'] for r in (current, previous)]
            for path in paths:
                sources = [self.git._git('show', revision + ':' + path, strip=False)
                           for revision in revisions]
                require(sources[0] == sources[1], 'Rollback retention protocol differs: ' + path)
        except Exception as exc:
            compatibility_error = str(exc)
        # Fence the final tombstone observation against collector publication.
        # Collector lock acquisition is nonblocking while it owns its DB tx.
        with FileLock(str(self.artifacts.root.parent / 'artifacts.lock'), timeout=30):
            with self.service.store.transaction() as tx:
                require(tx.get('deployment', 'active') == active, 'Stale rollback')
                blocked = bool(tx.scan('artifact_tombstones')) and compatibility_error is not None
                tx.put('maintenance_control', 'collection', {'status': 'paused',
                       'reason': 'rollback requires verified writer convergence', 'at': utcnow()})
            if not blocked:
                previous = self.releases.rollback(active['release_id'], reason)
                return {'status': 'rolled_back', 'active': previous}
        receipt = self.artifacts.put(canonical({'active': active, 'reason': reason,
            'compatibility_error': compatibility_error, 'paths': paths}), 'rollback-compatibility-blocked')
        return {'status': 'rollback_blocked', 'active': active, 'reason': compatibility_error,
                'evidence': receipt['ref']}

    def monitor(self) -> dict:
        with self.service.store.transaction() as tx:
            active = tx.get("deployment", "active")
            image = tx.get("images", active["release_id"]) if active else None
        if not image:
            return {"status": "no_deployment"}
        check = self._check(["docker", "run", "--rm", "--memory", "512m", "--entrypoint", "codex",
                             image["image"], "--version"], timeout=45)
        if not check["passed"]:
            return {**self.rollback_if_compatible(active, "External CLI health check failed"), 'check': check}
        running = run_process(["docker", "compose", "ps", "--format", "json"], cwd=str(self.git.repository), timeout=30)
        require(running.returncode == 0, "Cannot inspect deployed containers")
        for line in running.stdout.splitlines():
            if not line.startswith("{"):
                continue
            container = json.loads(line)
            if container.get("Service") not in {"conductor", "research-lead", "improvement-lead", "implementation-worker",
                                                 "github-worker", "geeknews-worker"}:
                continue
            inspection = run_process(["docker", "inspect", container["ID"], "--format", "{{.Image}}"], timeout=20)
            actual = run_process(["docker", "image", "inspect", image["image"], "--format", "{{.Id}}"], timeout=20)
            if inspection.stdout.strip() != actual.stdout.strip():
                continue
            check = self._check(["docker", "exec", container["ID"], "codex", "--version"], timeout=30)
            if not check["passed"]:
                return {**self.rollback_if_compatible(active, "Deployed container CLI health check failed"),
                        'container': container['Service'], 'check': check}
        return {"status": "healthy", "checked_at": utcnow(), "check": check}
