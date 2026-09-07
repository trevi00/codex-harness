import copy
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.skill_history import prepare_history
from codex_harness.adapters.store import MemoryStore, PostgresStore
from codex_harness.application.skill_history import SkillHistory
from codex_harness.domain.model import ContextItem, ContractError, canonical, digest
from codex_harness.domain.skill_history import assess_history


def event(key, score=1, content='sha256:' + 'a' * 64):
    return {'id': key, 'manifest_ref': 'sha256:' + 'b' * 64,
            'context_ref': 'sha256:' + 'c' * 64,
            'top': [{'path': 'python/broad.md', 'content_ref': content, 'score': score}]}


def test_thresholds_and_content_version_scope():
    events = [event(str(i)) for i in range(3)]
    current = events[0]['top']
    assert not assess_history(events[:2], current)[0]['candidate']
    assert assess_history(events, current)[0]['candidate']
    assert not assess_history(events + [event('strong', 5)], current)[0]['candidate']
    assert assess_history(events + [event('strong', 5)], current, 'strong')[0]['candidate']
    assert assess_history(events, event('changed', content='new-body')['top']) == []


def test_transactional_dedup_conflicts_retention_and_lease_guard(monkeypatch):
    store = MemoryStore()
    history = SkillHistory(store)
    monkeypatch.setattr('codex_harness.application.skill_history.MAX_EVENTS', 2)
    assert history.record('project', event('first'))
    assert not history.record('project', event('first'))
    with pytest.raises(ContractError, match='Conflicting'):
        history.record('project', event('first', 5))
    for key in ['second', 'third']:
        history.record('project', event(key))
    assert not history.record('project', event('first'))  # dedup survives hot-window eviction
    with store.transaction() as tx:
        assert [e['id'] for e in tx.get('skill_history', 'project')['events']] == ['second', 'third']
    def rejected(tx):
        raise ContractError('Stale execution')
    with pytest.raises(ContractError, match='Stale'):
        history.record('project', event('stale'), rejected)
    assert history.record('project', event('stale'))
    assert history.snapshot('other-project', event('x')['top'], '') == []


def test_atomic_body_advisory_uses_prior_samples_and_preserves_source(tmp_path):
    store, artifacts = MemoryStore(), FileArtifacts(str(tmp_path / 'artifacts'))
    raw = artifacts.put('FULL BODY', 'fixture')
    path = '.harness/skills/python/broad.md'
    record = {'path': path, 'content_ref': raw['ref'], 'score': 5,
              'base_score': 5, 'tier': 'full'}
    manifest = artifacts.put(canonical({'skills': [record]}), 'fixture-manifest')
    history = SkillHistory(store)
    for index in range(3):
        prior = event(str(index), content=raw['ref'])
        prior['top'][0]['path'] = path
        history.record(digest('project'), prior)
    selection = {'manifest_ref': manifest['ref']}
    item = ContextItem('project-skill:' + path, 'FULL BODY', raw['ref'], 'a' * 40, 18)
    items, observation = prepare_history(store, artifacts, 'project', 'agent', 'task', 'objective',
                                         selection, [item])
    assert 'historical_advisory' in items[0].body
    assert items[0].source_ref == raw['ref']
    before = copy.deepcopy(selection)
    service, project, current = observation
    service.record(project, {**current, 'context_ref': 'context'})
    replay = {'manifest_ref': manifest['ref']}
    repeated, _ = prepare_history(store, artifacts, 'project', 'agent', 'task', 'objective', replay, [item])
    assert repeated == items and replay == before
    record['tier'] = 'pointer'
    pointer_manifest = artifacts.put(canonical({'skills': [record]}), 'pointer')
    unchanged, _ = prepare_history(store, artifacts, 'project', 'agent', 'pointer', 'objective',
        {'manifest_ref': pointer_manifest['ref']}, [item])
    assert unchanged == [item]


@pytest.mark.integration
def test_postgres_concurrent_duplicate_delivery_has_one_sample():
    if os.environ.get('HARNESS_INTEGRATION') != '1':
        pytest.skip('Integration environment required')
    store = PostgresStore(os.environ['HARNESS_DATABASE_URL'])
    history = SkillHistory(store)
    project = 'test-skill-history-' + uuid4().hex
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: history.record(project, event('same')), range(8)))
    assert sum(results) == 1
    assert history.snapshot(project, event('same')['top'], '')[0]['count'] == 1
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda i: history.record(project, event('distinct-' + str(i))),
                                range(12)))
    assert all(results)
    assert history.snapshot(project, event('same')['top'], '')[0]['count'] == 13
    with store.transaction() as tx:
        ids = {entry['id'] for entry in tx.get('skill_history', project)['events']}
    assert ids == {'same'} | {'distinct-' + str(i) for i in range(12)}


def test_invalid_observation_does_not_write_history():
    store = MemoryStore()
    history = SkillHistory(store)
    for field in ('manifest_ref', 'context_ref'):
        malformed = event('invalid')
        del malformed[field]
        with pytest.raises(ContractError, match='Missing skill evidence'):
            history.record('project', malformed)
    malformed = event('invalid')
    malformed['top'] = [None]
    with pytest.raises(ContractError, match='Invalid skill observation item'):
        history.record('project', malformed)
    assert store.data == {}
