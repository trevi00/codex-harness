import json
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace

from codex_harness.adapters.monitoring import safe_text
from codex_harness.adapters.monitoring_web import handler
from codex_harness.application.monitoring import Monitoring, initiatives


def test_completed_implementation_does_not_hide_blocked_review():
    now = datetime.now(timezone.utc)
    facts = {'tasks': [{'id': 'impl', 'correlation': 'goal', 'phase': 'implement',
                       'status': 'succeeded', 'created_at': now.isoformat(), 'objective': 'Improve'}],
             'decisions': [{'id': 'review', 'correlation': 'goal', 'phase': 'review_lead',
                           'status': 'blocked', 'reason': 'Cannot inspect candidate',
                           'created_at': now.isoformat()}], 'releases': []}
    result = initiatives(facts, now)[0]
    assert result['status'] == 'attention'
    assert result['reason'] == 'Cannot inspect candidate'
    assert result['stages'][-1]['status'] == 'waiting'
    facts['decisions'] = []
    assert initiatives(facts, now)[0]['status'] == 'awaiting_next_stage'


def test_failed_canary_and_expired_lease_are_attention_states():
    now = datetime.now(timezone.utc)
    facts = {'tasks': [{'id': 'impl', 'correlation': 'goal', 'phase': 'implement',
                       'status': 'running', 'revision': 'abc',
                       'lease_until': (now - timedelta(seconds=1)).isoformat()}],
             'decisions': [], 'releases': [{'id': 'release', 'revision': 'abc', 'status': 'rejected',
                                          'checks': {'cli': {'passed': False}}}]}
    result = initiatives(facts, now)[0]
    assert result['status'] == 'attention'
    assert result['stages'][1]['status'] == 'lease_expired'
    assert result['stages'][-2]['status'] == 'failed'


def test_expired_execution_and_stale_health_are_not_live():
    now = datetime.now(timezone.utc)
    facts = {'health': {'status': 'healthy', 'checked_at': (now - timedelta(minutes=3)).isoformat()},
             'agents': [{'id': 'worker'}], 'decisions': [],
             'tasks': [{'id': 'old', 'agent': 'worker', 'status': 'running',
                        'lease_until': (now - timedelta(seconds=1)).isoformat()},
                       {'id': 'new', 'agent': 'worker', 'status': 'queued'}]}
    result = Monitoring(SimpleNamespace(read=lambda: facts)).snapshot(now)
    assert result['operating_status'] == 'unknown'
    assert result['agents'][0]['work'] == []
    assert result['agents'][0]['expired_leases'] == 1
    assert result['agents'][0]['queued'] == 1
    assert result['task_counts']['running'] == 1


def test_credential_redaction():
    text = safe_text('postgresql://admin:secret@localhost/db Bearer abc token=def password=xyz')
    assert all(secret not in text for secret in ['secret', 'abc', 'def', 'xyz'])


def test_http_rejects_mutations_hosts_and_unavailable_snapshot(tmp_path):
    path = tmp_path / 'status.json'
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler(path))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(method, endpoint, headers=None):
        connection = HTTPConnection('127.0.0.1', server.server_port, timeout=3)
        try:
            connection.request(method, endpoint, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()
    try:
        assert request('GET', '/api/status')[0] == 503
        path.write_text(json.dumps({'sources': {}}))
        assert request('GET', '/api/status') == (200, b'{"sources": {}}')
        assert request('GET', '/api/status', {'Host': 'untrusted.example'})[0] == 403
        assert request('POST', '/api/status')[0] == 405
        assert request('GET', '/.env')[0] == 404
        assert request('GET', '/')[0] == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
