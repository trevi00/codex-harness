from dataclasses import replace

import pytest

from codex_harness.adapters import app_server
from codex_harness.domain.model import ContractError


def run_timeline(monkeypatch, tmp_path, timeline):
    clock = [0.0]
    pending = list(timeline)
    monkeypatch.setattr(app_server.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(app_server, 'POLICY', replace(app_server.POLICY, tool_wait_grace_seconds=3))
    server = app_server.AppServer(executable='protocol-fixture')
    monkeypatch.setattr(server, 'request', lambda *args, **kwargs: {
        'thread': {'id': 'thread'}, 'turn': {'id': 'turn'}})

    def receive(timeout, **kwargs):
        end = clock[0] + timeout
        if pending and pending[0][0] <= end:
            clock[0], event = pending.pop(0)
            return event
        clock[0] = end
        return None

    monkeypatch.setattr(server, '_receive', receive)
    return server.run('review', str(tmp_path), {'type': 'object'}, timeout=2), clock[0]


def tool(method, key='tool', thread='thread'):
    return {'method': 'item/' + method, 'params': {'threadId': thread, 'turnId': 'turn',
            'item': {'type': 'commandExecution', 'id': key, 'status': 'completed'}}}


def finish(at):
    return [(at, {'method': 'item/completed', 'params': {'threadId': 'thread', 'turnId': 'turn',
                   'item': {'type': 'agentMessage', 'id': 'answer', 'text': '{"accepted":true}'}}}),
            (at, {'method': 'turn/completed', 'params': {'threadId': 'thread', 'turnId': 'turn',
                   'turn': {'id': 'turn', 'status': 'completed'}}})]


def test_slow_tool_does_not_discard_a_completed_review(monkeypatch, tmp_path):
    result, elapsed = run_timeline(monkeypatch, tmp_path,
        [(0, tool('started')), (2.5, tool('completed')), *finish(3)])
    assert result['answer'] == {'accepted': True}
    assert result['tool_wait_credit_seconds'] == 2.5
    assert elapsed == 3


@pytest.mark.parametrize('events', [[], [(0, tool('started', thread='other'))]])
def test_idle_or_foreign_tools_receive_no_extra_budget(monkeypatch, tmp_path, events):
    with pytest.raises(ContractError, match='execution budget exceeded'):
        run_timeline(monkeypatch, tmp_path, [*events, *finish(3)])
    assert app_server.time.monotonic() == 2


def test_credit_is_shared_not_reset_by_duplicate_or_new_tools(monkeypatch, tmp_path):
    with pytest.raises(ContractError, match='execution budget exceeded'):
        run_timeline(monkeypatch, tmp_path, [(0, tool('started')), (0.5, tool('started')),
            (2, tool('completed')), (2, tool('started', 'second')), (5.1, tool('completed', 'second')),
            *finish(5.2)])
    assert app_server.time.monotonic() == 5


def test_hung_tool_still_has_a_hard_wall_clock_cap(monkeypatch, tmp_path):
    with pytest.raises(ContractError, match='execution budget exceeded'):
        run_timeline(monkeypatch, tmp_path, [(0, tool('started'))])
    assert app_server.time.monotonic() == 5


@pytest.mark.parametrize('missing', ['threadId', 'turnId'])
def test_unattributed_tool_events_do_not_extend_budget(monkeypatch, tmp_path, missing):
    event = tool('started')
    del event['params'][missing]
    with pytest.raises(ContractError, match='execution budget exceeded'):
        run_timeline(monkeypatch, tmp_path, [(0, event), *finish(3)])
    assert app_server.time.monotonic() == 2
