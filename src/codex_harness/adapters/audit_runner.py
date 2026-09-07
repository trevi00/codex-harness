"""Acquire inert Git objects and inspect an isolated, ephemeral source tree."""
from __future__ import annotations

import base64
import os
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from codex_harness.adapters.commands import run_process
from codex_harness.adapters.source_verification import GitSourceVerifier
from codex_harness.domain.model import canonical, digest, require
from codex_harness.domain.research import ExecutionReceipt, InventoryEntry, SourceIdentity


class AuditRunner:
    def __init__(self, root, artifacts):
        self.root, self.artifacts = Path(root), artifacts
        self.root.mkdir(parents=True, exist_ok=True)

    def acquire(self, repository, commit):
        provisional = SourceIdentity(repository, commit, '0' * 40, 'sha256:' + '0' * 64)
        provisional.validate()
        target = self.root / digest({'repository': repository, 'commit': commit})
        from filelock import FileLock
        with FileLock(str(target) + '.lock', timeout=120):
            if not target.exists():
                target.mkdir()
                subprocess.run(['git', 'init', '--bare', str(target)], check=True, capture_output=True)
                subprocess.run(['git', '-C', str(target), 'remote', 'add', 'origin', repository],
                               check=True, capture_output=True)
            verifier = GitSourceVerifier(target, self.artifacts)
            verifier.git('-c', 'protocol.file.allow=never', '-c', 'protocol.ext.allow=never',
                         'fetch', '--no-tags', '--depth=1', 'origin', commit)
            source = replace(provisional, tree=verifier.git('rev-parse', commit + '^{tree}').decode().strip())
            entries = verifier.inventory(source)
            manifest = {'version': 1, 'repository': repository, 'commit': commit,
                        'tree': source.tree, 'entries': entries}
            source = replace(source, manifest_ref=self.artifacts.put(canonical(manifest), repository)['ref'])
            return source, [InventoryEntry(**e) for e in entries], verifier

    def execute(self, source, command):
        require(isinstance(command, list) and command and all(isinstance(c, str) and c for c in command),
                'Invalid inspection command')
        manifest = self.artifacts.document(source.manifest_ref)
        require(all(manifest[k] == getattr(source, k) for k in ('repository', 'commit', 'tree')),
                'Runner manifest mismatch')
        # INV-RESEARCH-003: never mount the active harness, credentials or artifact store.
        # Symlinks and gitlinks remain inert files; commands cannot follow upstream links.
        with tempfile.TemporaryDirectory(prefix='inspection-', dir=self.root) as directory:
            checkout = Path(directory)
            for entry in manifest['entries']:
                path = checkout / os.fsdecode(base64.b64decode(entry['path']))
                require(checkout in path.resolve().parents, 'Unsafe source path')
                path.parent.mkdir(parents=True, exist_ok=True)
                if entry['mode'] != '160000':
                    raw = self.artifacts.document(entry['artifact_ref'])
                    path.write_bytes(base64.b64decode(raw['data'], validate=True))
                    path.chmod(0o755 if entry['mode'] == '100755' else 0o644)
            argv = ['bwrap', '--unshare-all', '--die-with-parent', '--new-session',
                    '--clearenv', '--setenv', 'PATH', '/usr/local/bin:/usr/bin:/bin',
                    '--ro-bind', '/usr', '/usr', '--ro-bind', '/bin', '/bin']
            for lib in ('/lib', '/lib64'):
                if Path(lib).exists():
                    argv += ['--ro-bind', lib, lib]
            argv += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
                     '--ro-bind', directory, '/source', '--chdir', '/source', '--', *command]
            try:
                result = run_process(argv, timeout=120)
                output = {'argv': argv, 'stdout': result.stdout, 'stderr': result.stderr,
                          'exit_status': result.returncode}
                status = result.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                output, status = {'argv': argv, 'error': str(exc)}, 125
            blocked = status != 0 and ('bwrap:' in canonical(output) or status == 125)
            ref = self.artifacts.put(canonical(output), 'isolated-inspection')['ref']
            return ExecutionReceipt(source, digest({'runner': 'bubblewrap-v1', 'platform': os.uname()}),
                command, 'bubblewrap-unshare-all-readonly-source-inert-links', status, ref,
                'harness:isolated-source-runner-v1', blocked)
