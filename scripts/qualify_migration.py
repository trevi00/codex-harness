"""Run with the isolated checkout's Python -I; never starts the live supervisor."""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    for name in ('controller', 'candidate', 'policy-hash', 'release-id', 'repository',
                 'runtime', 'auth'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    # INV-RELEASE-001: inspect Git before importing any controller package.
    def git(*argv):
        return subprocess.check_output(['git', '-C', str(root), *argv]).decode().strip()

    if not sys.flags.isolated or git('rev-parse', 'HEAD') != args.controller:
        raise RuntimeError('Use Python -I from the exact reviewed controller checkout')
    if git('status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError('Controller checkout must be clean')
    os.chdir(root)
    sys.path.insert(0, str(root / 'src'))
    from codex_harness.adapters.artifacts import FileArtifacts
    from codex_harness.adapters.deployment import ReleaseRunner
    from codex_harness.adapters.git import GitWorkspace
    from codex_harness.application.qualification import qualify
    from codex_harness.bootstrap import build
    from codex_harness.domain.model import canonical

    service = build()
    artifacts = FileArtifacts(str(Path(args.runtime) / 'artifacts'))
    git_workspace = GitWorkspace(args.repository, str(Path(args.runtime) / 'workspaces'), remote=None)
    runner = ReleaseRunner(service, git_workspace, artifacts, args.auth, auto_merge=False)
    result = qualify(runner, args.release_id, args.candidate, args.policy_hash, args.controller)
    receipt = artifacts.put(canonical({'controller': args.controller, 'candidate': args.candidate,
        'policy_hash': args.policy_hash, 'release_id': args.release_id, 'result': result}),
        'migration-qualification')
    print(canonical({'result': result, 'receipt': receipt}))


if __name__ == '__main__':
    main()
