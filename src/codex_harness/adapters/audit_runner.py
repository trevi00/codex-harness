"""Acquire inert Git objects and inspect an isolated, ephemeral source tree."""
from __future__ import annotations

import base64
import os
import platform
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from codex_harness.adapters.commands import run_process
from codex_harness.adapters.source_verification import GitSourceVerifier
from codex_harness.domain.model import canonical, digest, require
from codex_harness.domain.research import ExecutionReceipt, InventoryEntry, SourceIdentity


class AuditRunner:
    def __init__(self, root, artifacts, host_execution=False):
        self.root, self.artifacts = Path(root), artifacts
        self.host_execution = host_execution
        self.root.mkdir(parents=True, exist_ok=True)

    def execute_assigned(self, source, command, task, workflow):
        if self.host_execution and command[0] not in {'source-list', 'source-read'}:
            from codex_harness.adapters.source_execution import SourceExecutionClient
            return SourceExecutionClient().execute(workflow, task, source, command)
        return self.execute(source, command)

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
            present = subprocess.run(['git', '-C', str(target), 'cat-file', '-e', commit + '^{commit}'],
                                     capture_output=True, timeout=30).returncode == 0
            if not present:
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
        # INV-RESEARCH-003: these built-ins inspect inert objects, never execute source code.
        if command[0] in {'source-list', 'source-read'}:
            import hashlib
            if command[0] == 'source-list':
                require(len(command) in {1, 2}, 'Invalid source-list arguments')
                start = int(command[1]) if len(command) == 2 else 0
                require(start >= 0, 'Invalid inventory offset')
                output = {'entries': manifest['entries'][start:start + 100],
                          'total': len(manifest['entries']), 'next_offset': start + 100}
            else:
                require(len(command) == 3, 'Use source-read BASE64_PATH START_LINE')
                entry = next((e for e in manifest['entries'] if e['path'] == command[1]), None)
                require(entry is not None and entry['mode'] != '160000', 'Unknown or submodule path')
                envelope = self.artifacts.document(entry['artifact_ref'])
                raw = base64.b64decode(envelope['data'], validate=True)
                require(hashlib.sha256(raw).hexdigest() == envelope['bytes_sha256'], 'Invalid source bytes')
                start = int(command[2])
                require(start >= 0, 'Invalid source line offset')
                lines = raw.decode('utf-8', errors='replace').splitlines()
                selected, size = [], 0
                for line in lines[start:start + 120]:
                    size += len(line.encode('utf-8'))
                    if size > 24000:
                        break
                    selected.append(line)
                output = {'path': entry['path'], 'lines': selected, 'start_line': start,
                          'next_line': start + len(selected), 'total_lines': len(lines),
                          'object_id': entry['object_id'], 'bytes_sha256': envelope['bytes_sha256']}
            ref = self.artifacts.put(canonical(output), 'inert-source-inspection')['ref']
            return ExecutionReceipt(source, digest({'runner': 'inert-source-reader-v1'}), command,
                                    'inert-objects-no-code-execution', 0, ref,
                                    'harness:inert-source-reader-v1', False)
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
            return ExecutionReceipt(source, digest({'runner': 'bubblewrap-v1', 'platform': platform.uname()}),
                command, 'bubblewrap-unshare-all-readonly-source-inert-links', status, ref,
                'harness:isolated-source-runner-v1', blocked)
