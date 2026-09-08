import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

from codex_harness.adapters.artifacts import FileArtifacts

root = Path.cwd()
artifacts = FileArtifacts(root / '.runtime/artifacts')
source = root / '.runtime/audit-sources/6e55570bfd7748f2c85fead85d699309899d909fe977db5b1d854aef55afe71a'
pin = 'b9586c59c062457a45018e41c2e753934b5ca6c9'
probe = Path(__file__).with_name('baldrix_budget_probe.py')
paths = ['scripts/lib/budget.py', 'scripts/lib/atomic_json.py', 'scripts/lib/paths.py',
         'scripts/lib/telemetry_log.py', 'scripts/lib/event_taxonomy.py', 'scripts/lib/event_store.py',
         'scripts/handlers/post_tool/agent_outcome_audit.py']
archive = subprocess.check_output(['git', '-c', 'core.autocrlf=false', '--git-dir', str(source), 'archive', pin])
with tempfile.TemporaryDirectory(prefix='baldrix-budget-probe-') as folder:
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(folder, filter='data')
    bindings = []
    for path in paths:
        body = subprocess.check_output(['git', '--git-dir', str(source), 'show', pin + ':' + path])
        assert (Path(folder) / path).read_bytes() == body
        bindings.append({'path': path, 'source_ref': artifacts.put(body.decode('utf-8'), 'baldrix-source:' + path)['ref']})
    argv = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--pids-limit', '64', '--memory', '512m', '--cpus', '1',
            '--tmpfs', '/tmp:rw,size=64m', '-e', 'PYTHONDONTWRITEBYTECODE=1',
            '-e', 'PYTHONPATH=/source/scripts', '-e', 'CLAUDE_HOME=/tmp/claude',
            '-e', 'CLAUDE_STATE_DIR=/tmp/state', '-e', 'CLAUDE_TELEMETRY_DIR=/tmp/telemetry',
            '--mount', f'type=bind,source={folder},target=/source,readonly',
            '--mount', f'type=bind,source={probe},target=/probe.py,readonly',
            '--entrypoint', 'python',
            'sha256:a23534401b82ff6075822d9b111f5f78f5a7f518b0a9d30fbb111611cd6988a0', '/probe.py']
    result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=90)
    receipt = artifacts.put(json.dumps({'source_revision': pin, 'bindings': bindings,
        'runner_ref': artifacts.put(Path(__file__).read_text('utf-8'), 'baldrix-budget-probe-runner')['ref'],
        'archive_sha256': hashlib.sha256(archive).hexdigest(),
        'probe_ref': artifacts.put(probe.read_text('utf-8'), 'baldrix-budget-probe')['ref'],
        'argv': argv, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
        'scope': 'Ten characterization probes, including direct hook subprocess stdin; passing includes defect reproduction, not fixes or native CLI hook qualification.'}),
        'baldrix-budget-probe-execution')
    (root / '.runtime/baldrix-budget-probe.json').write_text(json.dumps(receipt))
    print(json.dumps(receipt))
    print(result.stdout)
    print(result.stderr)
