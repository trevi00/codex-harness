import json
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace

from codex_harness.adapters.monitoring import safe_text
from codex_harness.adapters.monitoring_web import handler
from codex_harness.application.monitoring import Monitoring


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
