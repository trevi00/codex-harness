"""Passive Baldrix M7 score/dimension audit, with version-scoped identities."""
import math
import re
from collections import Counter
from datetime import datetime, timezone
from statistics import median

from codex_harness.domain.model import require
from codex_harness.domain.skill_history import (
    MAX_EVENTS,
    MIN_SAMPLES,
    THIN_SCORE_CEILING,
    is_candidate,
)

DIMENSIONS = ('intent', 'path', 'kw', 'pat')


def duration_seconds(value):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([smhd])', value.lower())
    require(match is not None, 'Invalid duration; use a positive number followed by s/m/h/d')
    result = float(match[1]) * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[match[2]]
    require(math.isfinite(result) and result > 0, 'Duration must be finite and positive')
    return result


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.replace(tzinfo=timezone.utc).timestamp() if parsed.tzinfo is None else parsed.timestamp()
    except (ValueError, OverflowError, OSError):
        return None


def audit_history(events, *, min_samples=MIN_SAMPLES, cutoff=None):
    require(isinstance(min_samples, int) and not isinstance(min_samples, bool) and min_samples > 0,
            'Minimum samples must be a positive integer')
    require(cutoff is None or math.isfinite(cutoff), 'Invalid time cutoff')
    scores, dimensions, overall = {}, {}, Counter()
    invocations = unknown_dates = invalid_entries = 0
    for event in events[-MAX_EVENTS:]:
        when = timestamp(event.get('at'))
        if cutoff is not None and when is not None and when < cutoff:
            continue
        invocations += 1
        unknown_dates += when is None
        for entry in event.get('top') or []:
            if (not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) and entry[k]
                    for k in ('path', 'content_ref')) or not isinstance(entry.get('score'), int)
                    or isinstance(entry['score'], bool) or entry['score'] < 0):
                invalid_entries += 1
                continue
            identity = (entry['path'], entry['content_ref'])
            scores.setdefault(identity, []).append(entry['score'])
            counts = dimensions.setdefault(identity, Counter())
            for dim in entry.get('dimensions') or []:
                category = dim.split(':', 1)[0] if isinstance(dim, str) and ':' in dim else 'unknown'
                category = category if category in DIMENSIONS else 'unknown'
                counts[category] += 1
                overall[category] += 1
    skills, candidates = [], []
    for identity, values in scores.items():
        count, middle = len(values), median(values)
        rate = sum(score <= THIN_SCORE_CEILING for score in values) / count
        dims = dimensions[identity]
        dominant = dims.most_common(1)[0][0] if dims else None
        record = {'path': identity[0], 'content_ref': identity[1], 'count': count,
                  'score_min': min(values), 'score_median': middle, 'score_max': max(values),
                  'thin_rate': round(rate, 3), 'dominant_dim': dominant, 'dim_breakdown': dict(dims)}
        skills.append(record)
        if is_candidate(count, rate, middle, min_samples):
            candidates.append({**record, 'reason': f'fires {count}x but {round(rate * 100)}% are thin '
                f'(score<={THIN_SCORE_CEILING}, never full-body); median {middle}. Narrow the '
                f'{dominant or "matching"} surface.'})
    def order(row):
        return -row['count'], row['path'], row['content_ref']
    return {'invocations': invocations, 'skills': sorted(skills, key=order),
            'false_positive_candidates': sorted(candidates, key=order), 'dim_weight': dict(overall),
            'unknown_timestamp_events': unknown_dates, 'invalid_entries': invalid_entries,
            'max_events': MAX_EVENTS, 'min_samples': min_samples, 'read_only': True}
