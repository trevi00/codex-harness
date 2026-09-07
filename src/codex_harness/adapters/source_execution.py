"""Host-owned Docker execution with no source-agent Docker socket or credentials."""
import base64
import hashlib
import os
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from uuid import uuid4

from codex_harness.adapters.commands import run_process
from codex_harness.application.source_execution import SourceExecutions
from codex_harness.domain.model import ContractError, canonical, digest, require
from codex_harness.domain.policy import POLICY
from codex_harness.domain.research import ExecutionReceipt, SourceIdentity


class SourceExecutionClient:
    def execute(self, workflow, task, source, command, timeout=POLICY.source_request_seconds):
        queue = SourceExecutions(workflow)
        request = queue.request(task, source, command)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with workflow.store.transaction() as tx:
                workflow._owned(tx, task)
                row = tx.get('source_execution_requests', request['id'])
            require(row['status'] != 'cancelled', 'Source execution cancelled')
            if row['status'] == 'succeeded':
                body = dict(row['receipt'])
                body['source'] = SourceIdentity(**body['source'])
                return ExecutionReceipt(**body)
            time.sleep(1)
        raise TimeoutError('Host source execution did not complete within its budget')


def bounded_command(argv, timeout):
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    tails = [b'', b'']
    def drain(stream, index):
        while block := stream.read(4096):
            tails[index] = (tails[index] + block)[-POLICY.source_output_bytes:]
    readers = [threading.Thread(target=drain, args=(stream, i), daemon=True)
               for i, stream in enumerate((process.stdout, process.stderr))]
    for thread in readers:
        thread.start()
    try:
        process.wait(timeout=timeout)
    except BaseException:
        process.kill()
        process.wait(timeout=10)
        raise
    finally:
        for thread in readers:
            thread.join(timeout=5)
    return subprocess.CompletedProcess(argv, process.returncode,
        tails[0].decode('utf-8', errors='replace'), tails[1].decode('utf-8', errors='replace'))


class DockerSourceRunner:
    def __init__(self, root, artifacts):
        self.root, self.artifacts = Path(root), artifacts
        self.root.mkdir(parents=True, exist_ok=True)

    def execute(self, source, command, image):
        source.validate()
        require(re.fullmatch(r'sha256:[0-9a-f]{64}', image) is not None, 'Immutable runner image required')
        require(command and all(isinstance(arg, str) and arg for arg in command), 'Invalid command')
        manifest = self.artifacts.document(source.manifest_ref)
        require(all(manifest[k] == getattr(source, k) for k in ('repository', 'commit', 'tree')),
                'Runner source mismatch')
        name = 'harness-source-' + uuid4().hex
        with tempfile.TemporaryDirectory(prefix='source-', dir=self.root) as directory:
            root = Path(directory).resolve()
            require(root.parent == self.root.resolve(), 'Temporary source root escaped workspace')
            try:
                seen = set()
                for entry in manifest['entries']:
                    name_bytes = os.fsdecode(base64.b64decode(entry['path'], validate=True))
                    if os.name == 'nt':
                        parts = name_bytes.split('/')
                        require(all(not re.search(r'[<>:"\\|?*\x00-\x1f]', part)
                                    and not part.endswith(('.', ' '))
                                    and part.split('.')[0].upper() not in
                                    {'CON', 'PRN', 'AUX', 'NUL', *[f'COM{i}' for i in range(10)],
                                     *[f'LPT{i}' for i in range(10)]} for part in parts),
                                'Source path cannot be represented on this host')
                    path = root / name_bytes
                    require(root in path.resolve().parents, 'Unsafe source path')
                    identity = os.path.normcase(str(path.resolve()))
                    require(identity not in seen, 'Source path collision on this host')
                    seen.add(identity)
                    if entry['mode'] == '160000':
                        continue
                    envelope = self.artifacts.document(entry['artifact_ref'])
                    raw = base64.b64decode(envelope['data'], validate=True)
                    require(hashlib.sha256(raw).hexdigest() == envelope['bytes_sha256'], 'Invalid source bytes')
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)  # Source symlinks remain inert regular files.
                    path.chmod(0o755 if entry['mode'] == '100755' else 0o644)
                argv = ['docker', 'run', '--rm', '--name', name, '--network', 'none',
                        '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                        '--memory', str(POLICY.source_memory_mb) + 'm', '--cpus', str(POLICY.source_cpus),
                        '--pids-limit', str(POLICY.source_pids),
                        '--tmpfs', '/tmp:rw,nosuid,size=' + str(POLICY.source_scratch_mb) + 'm', '-e', 'HOME=/tmp',
                        '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PYTHONPATH=/source',
                        '-v', str(root) + ':/source:ro', '-w', '/source',
                        '--entrypoint', '/usr/bin/timeout', image, str(POLICY.source_execution_seconds), *command]
                result = bounded_command(argv, timeout=POLICY.source_execution_seconds + 10)
                status = result.returncode
                output = {'argv': argv, 'stdout': result.stdout[-POLICY.source_output_bytes:],
                          'stderr': result.stderr[-POLICY.source_output_bytes:], 'exit_status': status,
                          'output_tail_limit_bytes': POLICY.source_output_bytes}
                blocked = status in {124, 125, 126, 127, 137}
            except (OSError, subprocess.TimeoutExpired, ContractError, ValueError) as exc:
                output, status, blocked = {'error': str(exc)}, 125, True
            finally:
                # Remove only this uniquely named container, including a timed-out Docker client.
                try:
                    run_process(['docker', 'rm', '-f', name], timeout=20)
                except (OSError, subprocess.TimeoutExpired):
                    pass  # The in-container deadline also bounds orphaned execution.
            ref = self.artifacts.put(canonical(output), 'host-isolated-source-execution')['ref']
        return ExecutionReceipt(source, digest({'image': image, 'runner': 'host-docker-v1'}), command,
            'docker-networkless-readonly-source-inert-links-no-credentials', status, ref,
            'harness:host-docker-source-runner-v1', blocked)

    def run_one(self, workflow):
        queue = SourceExecutions(workflow)
        row = queue.claim()
        if row:
            receipt = self.execute(SourceIdentity(**row['source']), row['command'], row['image'])
            queue.complete(row, receipt)
        return row
