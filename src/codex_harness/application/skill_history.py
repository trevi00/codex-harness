"""Bounded hot history, permanent small deduplication ledger, transactional writes."""
from codex_harness.domain.model import digest, require, utcnow
from codex_harness.domain.skill_history import MAX_EVENTS, TOP_MATCHES, assess_history


class SkillHistory:
    def __init__(self, store):
        self.store = store

    def snapshot(self, project, current, exclude):
        with self.store.transaction() as tx:
            state = tx.get('skill_history', project) or {'events': []}
        return assess_history(state['events'], current, exclude)

    def record(self, project, event, guard=None):
        require(all(isinstance(event.get(key), str) and event[key]
                    for key in ('manifest_ref', 'context_ref')), 'Missing skill evidence reference')
        require(isinstance(event.get('id'), str) and bool(event['id']), 'Missing skill observation id')
        require(isinstance(event.get('top'), list) and len(event['top']) <= TOP_MATCHES,
                'Invalid skill observation size')
        for item in event['top']:
            require(isinstance(item, dict), 'Invalid skill observation item')
            require(isinstance(item.get('score'), int) and not isinstance(item['score'], bool)
                    and item['score'] >= 0, 'Invalid skill score')
            require(all(isinstance(item.get(key), str) and item[key]
                        for key in ('path', 'content_ref')), 'Invalid skill identity')
        require(len({(r['path'], r['content_ref']) for r in event['top']}) == len(event['top']),
                'Duplicate skill identity in observation')
        fingerprint = digest({key: event[key] for key in ('id', 'top', 'manifest_ref')})
        key = digest([project, event['id']])
        with self.store.transaction() as tx:
            if guard:
                guard(tx)
            prior = tx.get('skill_observations', key)
            if prior:
                require(prior['fingerprint'] == fingerprint, 'Conflicting skill observation replay')
                return False
            state = tx.get('skill_history', project) or {'events': []}
            state['events'] = (state['events'] + [event])[-MAX_EVENTS:]
            tx.put('skill_history', project, state)
            tx.put('skill_observations', key, {'fingerprint': fingerprint,
                   'context_ref': event['context_ref'], 'at': utcnow()})
        return True
