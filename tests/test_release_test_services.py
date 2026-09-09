"""Real Docker environment/cleanup test; explicitly enabled on the release host."""
import os
import sys
from pathlib import Path

import psycopg
import pytest
import redis

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.commands import run_process
from codex_harness.adapters.release_test_services import isolated_release_services


@pytest.mark.integration
@pytest.mark.skipif(os.environ.get('HARNESS_DOCKER_INTEGRATION') != '1',
                    reason='Requires Docker-capable qualification host')
def test_release_services_are_initialized_isolated_and_cleaned_on_failure(tmp_path):
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    root = str(Path(__file__).resolve().parents[1])
    with pytest.raises(RuntimeError, match='intentional body failure'):
        with isolated_release_services(sys.executable, root, artifacts) as env:
            assert env['HARNESS_DATABASE_URL'] != os.environ.get('HARNESS_DATABASE_URL')
            assert env['HARNESS_REDIS_URL'] != os.environ.get('HARNESS_REDIS_URL')
            with psycopg.connect(env['HARNESS_DATABASE_URL']) as connection:
                assert connection.execute("SELECT to_regclass('documents')").fetchone()[0]
            assert redis.Redis.from_url(env['HARNESS_REDIS_URL']).ping()
            raise RuntimeError('intentional body failure')
    receipts = [artifacts.document('sha256:' + p.stem) for p in artifacts.root.glob('*.txt')]
    receipt = receipts[0]
    assert len(receipt['cleanup']) == 2
    for item in receipt['cleanup']:
        assert item['exit_code'] == 0
        assert run_process(['docker', 'inspect', item['name']]).returncode != 0
