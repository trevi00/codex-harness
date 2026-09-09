"""Git-owned, exact command-output occurrence bindings (INV-RESOURCE-001)."""

import hashlib
import json
import re
from importlib.resources import files

from codex_harness.adapters.historical_provenance import CombinedProvenance, HistoricalCopies
from codex_harness.domain.model import require


def _unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate provenance JSON key')
        result[key] = value
    return result


def _hash(data):
    return hashlib.sha256(data).hexdigest()


class OccurrenceProvenance:
    """Snapshot annotations once; runtime metadata cannot supply approvals.

    V1 deliberately supports only synthetic tokens in authenticated completed
    command output and its exact deltas. Arbitrary copied summaries stay edges.
    """

    def __init__(self, data):
        self.revision = _hash(data)
        document = json.loads(data, object_pairs_hook=_unique)
        require(set(document) == {'version', 'occurrences'}
                and type(document['version']) is int and document['version'] == 1
                and isinstance(document['occurrences'], list), 'Unknown occurrence schema')
        self._entries = {}
        for entry in document['occurrences']:
            require(isinstance(entry, dict) and set(entry) == {
                'parent', 'origin_event', 'target_event', 'output_offset', 'start', 'end',
                'namespace', 'hex', 'command_hex', 'output_hex', 'expression',
            }, 'Unknown occurrence fields')
            require(all(type(entry[k]) is int and entry[k] >= 0 for k in (
                'origin_event', 'target_event', 'output_offset', 'start', 'end')),
                'Invalid occurrence interval')
            require(isinstance(entry['parent'], str)
                    and re.fullmatch(r'sha256:[0-9a-f]{64}', entry['parent'])
                    and all(isinstance(entry[k], str) and re.fullmatch(r'[0-9a-f]{64}', entry[k])
                            for k in ('hex', 'command_hex', 'output_hex')),
                    'Invalid occurrence identity')
            require(entry['namespace'] == 'isolated-test-token'
                    and len(set(entry['hex'])) == 1
                    and entry['expression'] == "'sha256:'+'" + entry['hex'][0] + "'*64",
                    'Unsupported occurrence namespace or expression')
            self._entries.setdefault(entry['parent'], []).append(dict(entry))

    def project(self, parent, content):
        entries = self._entries.get(parent)
        if not entries:
            return content, set()
        require(_hash(content) == parent[7:], 'Stale occurrence parent')
        document = json.loads(content, object_pairs_hook=_unique)
        changes = {}
        try:
            for entry in entries:
                origin = document['events'][entry['origin_event']]
                params = origin['params']
                item = params['item']
                output = item['aggregatedOutput'].encode('utf-8')
                require(origin['method'] == 'item/completed'
                        and item['type'] == 'commandExecution' and item['status'] == 'completed'
                        and type(item['exitCode']) is int and item['exitCode'] == 0
                        and _hash(item['command'].encode()) == entry['command_hex']
                        and _hash(output) == entry['output_hex']
                        and entry['expression'] in item['command'], 'Invalid occurrence origin')
                target = document['events'][entry['target_event']]
                target_params = target['params']
                require(all(isinstance(params[k], str) and target_params[k] == params[k]
                            for k in ('threadId', 'turnId')), 'Occurrence stream mismatch')
                if entry['target_event'] == entry['origin_event']:
                    owner, key = item, 'aggregatedOutput'
                else:
                    require(target['method'] == 'item/commandExecution/outputDelta'
                            and target_params['itemId'] == item['id'], 'Unknown occurrence target')
                    owner, key = target_params, 'delta'
                scalar = owner[key].encode('utf-8')
                offset = entry['output_offset']
                require(output[offset:offset + len(scalar)] == scalar, 'Unbound output copy')
                start, end = entry['start'], entry['end']
                require(end == start + 71 and scalar[start:end] == (
                    'sha256:' + entry['hex']).encode(), 'Stale occurrence interval')
                # Validate UTF-8 boundaries before applying any projection.
                scalar[:start].decode('utf-8')
                scalar[end:].decode('utf-8')
                group = changes.setdefault(entry['target_event'], (owner, key, scalar, []))
                require(all(end <= left or start >= right for left, right in group[3]),
                        'Overlapping occurrence intervals')
                group[3].append((start, end))
        except (KeyError, IndexError, TypeError, AttributeError, UnicodeError) as exc:
            raise ValueError('Invalid occurrence selector') from exc
        for owner, key, scalar, intervals in changes.values():
            for start, end in sorted(intervals, reverse=True):
                scalar = scalar[:start] + b'TEST_TOKEN:' + scalar[start + 7:end] + scalar[end:]
            owner[key] = scalar.decode('utf-8')
        # Origin is this immutable execution artifact, even for output deltas.
        # Keep it mandatory; a self edge terminates naturally in the mark set.
        return json.dumps(document, ensure_ascii=False).encode('utf-8'), {parent}


# Process-local immutable snapshot. Resource edits require a fresh writer/collector
# process and release qualification; they cannot change an in-flight scan.
PROVENANCE = CombinedProvenance(
    OccurrenceProvenance(
        files('codex_harness.resources').joinpath('occurrence-provenance.v1.json').read_bytes()),
    HistoricalCopies(
        files('codex_harness.resources').joinpath('occurrence-copies.v1.json').read_bytes()))
