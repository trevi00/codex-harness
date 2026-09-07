import copy
import json
from pathlib import Path

import pytest

from codex_harness.adapters.app_server import AppServer
from codex_harness.domain.model import ContractError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'harness_hooks/hook-ab97ba09554daa5aec289867.json').read_text())
SCHEMA = {'type': 'object', 'properties': {'accepted': {'type': 'boolean'}}, 'required': ['accepted']}


def replay(monkeypatch, events, *, hooks=None, discovered=None, read_only=True):
    server = AppServer(executable='fixture', hooks=hooks)
    requests = []

    def request(method, params, *args):
        requests.append((method, params))
        if method == 'hooks/list':
            return {'data': [{'hooks': discovered or []}]}
        return {'thread': {'id': 'thread'}, 'turn': {'id': 'turn'}}

    monkeypatch.setattr(server, 'request', request)
    monkeypatch.setattr(server, '__exit__', lambda: None)
    monkeypatch.setattr(server, '__enter__', lambda: server)
    incoming = iter(events)
    monkeypatch.setattr(server, '_receive', lambda *a, **k: next(incoming))
    observed = []
    result = server.run('quoted bwrap: No permissions to create a new namespace', str(ROOT),
                        SCHEMA, read_only=read_only, on_event=observed.append)
    return result, requests, observed, server


def finish(text='{"accepted":true}', status='completed'):
    return [
        {'method': 'item/completed', 'params': {'threadId': 'thread', 'turnId': 'turn',
         'item': {'type': 'agentMessage', 'id': 'answer', 'text': text}}},
        {'method': 'turn/completed', 'params': {'threadId': 'thread',
         'turn': {'id': 'turn', 'status': status}}},
    ]


def failure():
    event = copy.deepcopy(MANIFEST['cases']['reproduction'][0]['input'])
    event['params'].update(threadId='thread', turnId='turn')
    return event


@pytest.mark.parametrize('text,status', [('{"accepted":true}', 'completed'),
                                        ('malformed verdict', 'completed'), ('', 'interrupted'),
                                        ('', 'failed')])
def test_actual_startup_failure_overrides_verdict_and_preserves_evidence(monkeypatch, text, status):
    event = failure()
    result, requests, observed, _ = replay(monkeypatch, [event, event, *finish(text, status)])
    assert result['inspection_blocked'] and result['answer'] is None
    assert result['inspection_failures'] == [event]
    assert result['model_answer_text'] == text
    assert observed[:2] == [event, event]
    options = next(p for m, p in requests if m == 'thread/start')
    assert options['sandbox'] == 'danger-full-access' and options['approvalPolicy'] == 'never'
    assert 'do not edit tracked source' in options['developerInstructions']


@pytest.mark.parametrize('change', [{'exitCode': 0, 'status': 'completed'},
                                    {'aggregatedOutput': 'Permission denied'}])
def test_normal_review_completion(monkeypatch, change):
    event = failure()
    event['params']['item'].update(change)
    result, *_ = replay(monkeypatch, [event, *finish()])
    assert result['answer'] == {'accepted': True}
    assert not result.get('inspection_blocked')


def test_other_thread_and_old_turn_are_excluded(monkeypatch):
    other, old = failure(), failure()
    other['params']['threadId'] = 'other'
    old['params']['turnId'] = 'old'
    result, *_ = replay(monkeypatch, [other, old, *finish()])
    assert result['answer']['accepted']


def test_implementation_execution_is_not_a_review(monkeypatch):
    result, *_ = replay(monkeypatch, [failure(), *finish()], read_only=False)
    assert result['answer']['accepted']


def test_verified_native_hook_discovery(monkeypatch):
    hooks = {'SessionStart': [{'matcher': 'startup', 'hooks': [{'command': 'python fixture'}]}]}
    entry = {'handler': {'command': 'python fixture'}, 'key': 'fixture-key', 'currentHash': 'hash'}
    result, requests, _, server = replay(monkeypatch, finish(), hooks=hooks, discovered=[entry])
    assert result['answer']['accepted']
    assert requests[0][0] == 'hooks/list'
    assert server.hook_state == {'fixture-key': {'enabled': True, 'trusted_hash': 'hash'}}
    with pytest.raises(ContractError, match='did not discover'):
        replay(monkeypatch, finish(), hooks=hooks)


@pytest.mark.parametrize('ending', ['eof', 'timeout'])
def test_transport_failure_without_inspection_failure_still_raises(monkeypatch, ending):
    server = AppServer(executable='fixture')
    monkeypatch.setattr(server, 'request', lambda *a, **k: {
        'thread': {'id': 'thread'}, 'turn': {'id': 'turn'}})
    if ending == 'eof':
        server.incoming.put(None)
    receive = server._receive
    monkeypatch.setattr(server, '_receive', lambda *a, **k: receive(0.01, poll=False))
    with pytest.raises(ContractError, match='exited unexpectedly|timed out'):
        server.run('review', str(ROOT), SCHEMA, read_only=True)
