"""Baldrix b9586c59 thin-skill predicate, scoped to immutable skill identities."""
from statistics import median

THIN_SCORE_CEILING = 2
MIN_SAMPLES = 3
FP_THIN_RATE = 0.8
MAX_EVENTS = 4000
TOP_MATCHES = 5


def is_candidate(count, thin_rate, middle, min_samples=MIN_SAMPLES):
    return count >= min_samples and thin_rate >= FP_THIN_RATE and middle <= THIN_SCORE_CEILING


def assess_history(events, current, exclude=None):
    identities = {(record['path'], record['content_ref']) for record in current}
    scores = {}
    for event in events[-MAX_EVENTS:]:
        if event['id'] == exclude:
            continue
        for record in event['top']:
            identity = (record['path'], record['content_ref'])
            if identity in identities:
                scores.setdefault(identity, []).append(record['score'])
    result = []
    for (path, content_ref), values in sorted(scores.items()):
        thin_rate = sum(score <= THIN_SCORE_CEILING for score in values) / len(values)
        middle = median(values)
        result.append({'path': path, 'content_ref': content_ref, 'count': len(values),
                       'median': middle, 'thin_rate': thin_rate,
                       'candidate': is_candidate(len(values), thin_rate, middle)})
    return result
