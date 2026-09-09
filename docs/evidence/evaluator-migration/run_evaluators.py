"""Local diagnostic runs, NOT authorized release qualification or real canaries."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main():
    from codex_harness.adapters.evaluator_migration import EVALUATOR, SOURCE_BASE

    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(OUT))
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    source_files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((ROOT / 'src').rglob('*'))
                    if p.is_file() and '__pycache__' not in p.parts}
    source_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    receipts = []
    for label, revision in [('legacy', SOURCE_BASE), ('proposed', EVALUATOR)]:
        checkout = Path(tempfile.mkdtemp(prefix='migration-' + label + '-', dir=ROOT / '.git'))
        subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(checkout)], check=True)
        subprocess.run(['git', '-C', str(checkout), 'checkout', '--quiet', '--detach', revision], check=True)
        shutil.rmtree(checkout / 'src')
        shutil.copytree(ROOT / 'src', checkout / 'src', ignore=shutil.ignore_patterns('__pycache__'))
        argv = [sys.executable, '-m', 'pytest', str(checkout / 'tests'), '-c',
                str(checkout / 'pyproject.toml'), '--import-mode=importlib', '-ra']
        result = subprocess.run(argv, cwd=checkout, capture_output=True,
                                env={**os.environ, 'PYTHONPATH': os.pathsep.join(
                                    [str(checkout / 'tests'), str(checkout / 'src')])})
        log = result.stdout + result.stderr
        (output / (label + '-full.log')).write_bytes(log)
        receipts.append({'scope': 'local diagnostic; proposed migration unapproved',
                         'evaluator_revision': revision, 'argv': argv, 'exit_code': result.returncode,
                         'log_sha256': hashlib.sha256(log).hexdigest(),
                         'label': label, 'candidate_revision': source_revision,
                         'candidate_source_sha256': source_files, 'integration': os.environ.get('HARNESS_INTEGRATION', 'disabled')})
        (output / 'evaluator-runs.json').write_text(json.dumps(receipts, indent=2) + '\n')
        shutil.rmtree(checkout)


if __name__ == '__main__':
    main()
