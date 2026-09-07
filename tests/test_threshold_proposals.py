from dataclasses import replace

import pytest

from codex_harness.domain.model import ContractError
from codex_harness.domain.threshold_proposals import (
    LOCKED_DENY,
    REGISTRY,
    direction_allowed,
    holdout_boundary,
    propose_threshold_changes,
    validate_registry,
)

NAME = 'skill_match.FULL_BODY_MIN_SCORE'


def corpus(score=3, sized=True):
    return [{'at': f'2026-01-01T00:00:{i:02d}Z',
             'top': [{'score': s, **({'body_chars': 500} if sized else {})} for s in [score, score + 2]]}
            for i in range(40)]


def propose(events, current=3, revision='a' * 40, **kwargs):
    return propose_threshold_changes(events_by_source={'skill-match': events},
        current_values={NAME: current}, policy_revision=revision, **kwargs)


def test_reference_proposal_generalizes_and_binds_effective_policy():
    proposal, = propose(corpus())
    assert proposal['suggested'] == 4 and proposal['reference_accepted']
    assert proposal['trailing_size'] == 28 and proposal['holdout_size'] == 12
    assert proposal['advisory_only'] and not proposal['activation_ready']
    assert propose(corpus()) == [proposal]
    assert propose(corpus(), revision='b' * 40)[0]['id'] != proposal['id']
    shifted, = propose(corpus(4), current=4)
    assert shifted['suggested'] == 5 and shifted['current'] == 4


def test_missing_sizes_and_non_generalizing_improvements_cannot_offer_apply():
    missing, = propose(corpus(sized=False))
    assert missing['suggested'] is None and not missing['reference_accepted']
    assert missing['report']['gate']['reason'] == 'non_finite_metric'
    events = corpus()
    for event in events[28:]:
        event['top'] = [{'score': 5, 'body_chars': 500}]
    rejected, = propose(events)
    assert rejected['suggested'] is None
    assert rejected['report']['gate']['target_delta_holdout'] == 0


def test_temporal_partition_and_sample_floors():
    assert propose(corpus()[:5]) == []
    assert holdout_boundary([{'at': None}]) is None
    assert propose([{'at': '2026-01-01T00:00:00Z'}] * 40) == []
    assert holdout_boundary([{'at': '2026-01-01T09:00:00+09:00'},
                             {'at': '2026-01-01T01:00:00Z'}]) == '2026-01-01T01:00:00+00:00'
    for invalid in [0, -1, True]:
        with pytest.raises(ContractError):
            propose(corpus(), min_sample=invalid)


def test_closed_registry_and_direction_enforcement(monkeypatch):
    validate_registry()
    assert len(REGISTRY) == 5 and len(LOCKED_DENY) == 12
    entry = replace(REGISTRY[NAME], direction_safety='raise_safe')
    assert direction_allowed(entry, 5, 6) and not direction_allowed(entry, 5, 4)
    monkeypatch.setitem(REGISTRY, NAME, replace(entry, qualified=next(iter(LOCKED_DENY))))
    with pytest.raises(ContractError, match='locked'):
        propose(corpus())


def test_no_implicit_default_or_unknown_policy():
    for values in [{}, {'unknown': 3}, {NAME: float('nan')}, {NAME: True}]:
        with pytest.raises(ContractError):
            propose_threshold_changes(events_by_source={}, current_values=values, policy_revision='a' * 40)
    with pytest.raises(ContractError, match='revision'):
        propose(corpus(), revision='unbound')
