"""Disposable integration services for host-controlled release qualification."""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from codex_harness.adapters.commands import run_process
from codex_harness.domain.model import canonical, require


@contextmanager
def isolated_release_services(python, cwd, artifacts):
    # INV-RELEASE-001: schema isolation alone does not isolate advisory locks.
    # Never supply the production database or Redis to adversarial integration tests.
    names, commands, cleanup = [], [], []

    def command(argv, timeout=60, env=None):
        result = run_process(argv, timeout=timeout, env=env, cwd=cwd)
        commands.append({'argv': argv, 'exit_code': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        require(result.returncode == 0, 'Release test service command failed: ' + argv[0])
        return result.stdout.strip()

    try:
        ports = []
        for kind, image, port in [('postgres', 'pgvector/pgvector:pg17', 5432),
                                  ('redis', 'redis:7.4-alpine', 6379)]:
            name = 'harness-release-test-' + kind + '-' + uuid4().hex[:12]
            names.append(name)  # Cleanup also covers partially successful creation.
            argv = ['docker', 'run', '-d', '--rm', '--name', name,
                    '-p', f'127.0.0.1::{port}']
            if kind == 'postgres':
                argv += ['--memory', '512m', '--cpus', '1',
                         '-e', 'POSTGRES_HOST_AUTH_METHOD=trust',
                         '--tmpfs', '/var/lib/postgresql/data:rw,size=256m']
            else:
                argv += ['--memory', '128m', '--tmpfs', '/data:rw,size=64m']
            command(argv + [image], timeout=180)
            binding = command(['docker', 'port', name, str(port) + '/tcp'])
            require(binding.startswith('127.0.0.1:') and '\n' not in binding,
                    'Release test port must bind only to loopback')
            ports.append(int(binding.rsplit(':', 1)[1]))
            command(['docker', 'inspect', name, '--format', '{{.Image}}'])
        for name, probe in zip(names, [['pg_isready'], ['redis-cli', 'ping']]):
            for _ in range(30):
                result = run_process(['docker', 'exec', name, *probe], timeout=5)
                if result.returncode == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError('Release test service readiness timed out: ' + name)
        env = {**os.environ, 'HARNESS_INTEGRATION': '1', 'HARNESS_DOCKER_INTEGRATION': '1',
               'PYTHONPATH': str(Path(cwd).resolve() / 'src'),
               'HARNESS_DATABASE_URL': f'postgresql://postgres@127.0.0.1:{ports[0]}/postgres',
               'HARNESS_REDIS_URL': f'redis://127.0.0.1:{ports[1]}/0'}
        # Use the selected candidate interpreter/schema, before any integration test.
        command([str(python), '-c', 'import os; from codex_harness.adapters.store '
                 'import PostgresStore; PostgresStore(os.environ["HARNESS_DATABASE_URL"]).migrate()'],
                env=env)
        yield env
    finally:
        for name in reversed(names):
            try:
                result = run_process(['docker', 'rm', '-f', name], timeout=30)
                cleanup.append({'name': name, 'exit_code': result.returncode,
                                'stderr': result.stderr})
            except Exception as exc:
                cleanup.append({'name': name, 'exit_code': -1, 'stderr': str(exc)})
        artifacts.put(canonical({'commands': commands, 'cleanup': cleanup,
                                 'scope': 'isolated release integration services'}),
                      'release-integration-environment')

        require(all(item['exit_code'] == 0 for item in cleanup),
                'Release test service cleanup incomplete; inspect environment receipt')
