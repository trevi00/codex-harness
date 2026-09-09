"""Bounded offline evidence preparation; output is a review draft, never approval."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
SOURCES = {
    'a23534401b82ff6075822d9b111f5f78f5a7f518b0a9d30fbb111611cd6988a0': [
        '34387bcb5a12d3f30db01a3672548efeaf3a1f6be802c9c195f33e0b5f073613',
        '52303f1f22318fbb6ba7de0b47f4cf6e137242c12fc0b74023ae53b236c390f6'],
    '1' * 64: ['4fe2f35b9494727f2409cc00763083869d8106434e02140c44d912f8ea86d0fd',
               'd4d820258190b7046e715d0d70c1a6df3a7cfc1b90c1af4ce5781c8a2dcd4b29',
               'eb56f9fd8f9bf13babf8c8e6360de6999fe2858412b7e4e15643b5c1b8ee949a'],
    '2' * 64: ['7746a7d290352e522e73e481ced8ab51f3a474f99fbc85b7b5618e2405f48dfe',
               'be0a89b15234f46da28627c293493598fa7a145d4a9f4ab2cb85706e79ecb67b'],
    'a' * 64: ['f83af829cfbdef93c0bc5f75901d453dedf9c0211450910115cf27536dc7098b'],
}
COMMANDS = {
    'd4d820258190b7046e715d0d70c1a6df3a7cfc1b90c1af4ce5781c8a2dcd4b29': 'exec-79b2a53c-14b6-4f32-a434-5e9b99f10f05',
    'be0a89b15234f46da28627c293493598fa7a145d4a9f4ab2cb85706e79ecb67b': 'exec-093a4347-f621-4b8d-a581-f7ef36771e84',
    'f83af829cfbdef93c0bc5f75901d453dedf9c0211450910115cf27536dc7098b': 'exec-8226115b-69bc-4522-92cf-6f5ee16d6975',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect(artifact_root):
    entries, observations = [], []
    for identifier, parents in SOURCES.items():
        for parent in parents:
            data = (artifact_root / (parent + '.txt')).read_bytes()
            assert len(data) < 1_000_000 and digest(data) == parent
            value = json.loads(data)
            token = ('sha256:' + identifier).encode()
            observation = {'parent': 'sha256:' + parent, 'bytes': len(data),
                           'identifier': {'namespace': 'unresolved', 'hex': identifier},
                           'raw_occurrences': [m.start() for m in re.finditer(token, data)],
                           'attested_occurrences': 0, 'status': 'blocked'}
            if parent in COMMANDS:
                events = value['events']
                origins = [(i, e) for i, e in enumerate(events)
                           if e.get('method') == 'item/completed'
                           and e.get('params', {}).get('item', {}).get('id') == COMMANDS[parent]]
                assert len(origins) == 1
                origin_index, origin = origins[0]
                params, item = origin['params'], origin['params']['item']
                output = item['aggregatedOutput'].encode()
                assert item['exitCode'] == 0 and item['status'] == 'completed'
                expression = "'sha256:'+'" + identifier[0] + "'*64"
                assert expression in item['command']
                raw_path = EVIDENCE / 'raw' / (parent + '.json')
                raw_path.write_text(json.dumps(origin, indent=2) + '\n')
                observation['origin'] = {'event': origin_index, 'item_id': item['id'],
                                         'raw_path': str(raw_path.relative_to(ROOT)),
                                         'raw_hex': digest(raw_path.read_bytes()),
                                         'command_hex': digest(item['command'].encode()),
                                         'output_hex': digest(output), 'expression': expression}
                for target_index, event in enumerate(events):
                    p = event.get('params', {})
                    if target_index == origin_index:
                        scalar, offset = output, 0
                    elif (event.get('method') == 'item/commandExecution/outputDelta'
                          and p.get('itemId') == item['id']
                          and all(p.get(k) == params[k] for k in ('threadId', 'turnId'))):
                        scalar = p['delta'].encode()
                        # Ambiguous or missing slices stay unannotated.
                        offset = output.find(scalar)
                        if not scalar or offset < 0 or output.find(scalar, offset + 1) >= 0:
                            continue
                    else:
                        continue
                    for match in re.finditer(token, scalar):
                        entries.append({'parent': 'sha256:' + parent,
                                        'origin_event': origin_index, 'target_event': target_index,
                                        'output_offset': offset, 'start': match.start(), 'end': match.end(),
                                        'namespace': 'isolated-test-token', 'hex': identifier,
                                        'command_hex': digest(item['command'].encode()),
                                        'output_hex': digest(output), 'expression': expression})
                        observation['attested_occurrences'] += 1
            observations.append(observation)
            # Per-parent checkpoint; a failed run never claims complete coverage.
            (EVIDENCE / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    (ROOT / 'src/codex_harness/resources/occurrence-provenance.v1.json').write_text(
        json.dumps({'version': 1, 'occurrences': entries}, indent=2) + '\n')
    from codex_harness.adapters.occurrence_provenance import OccurrenceProvenance
    bindings = OccurrenceProvenance(json.dumps({'version': 1, 'occurrences': entries}).encode())
    for observation in observations:
        parent = observation['parent']
        data = (artifact_root / (parent[7:] + '.txt')).read_bytes()
        projected, _ = bindings.project(parent, data)
        token = 'sha256:' + observation['identifier']['hex']
        remaining = []

        def walk(value, pointer=''):
            if isinstance(value, dict):
                for key, child in value.items():
                    walk(child, pointer + '/' + key.replace('~', '~0').replace('/', '~1'))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, pointer + '/' + str(index))
            elif isinstance(value, str) and token in value:
                start = value.index(token)
                excerpt = value[max(0, start - 80):start + 151]
                remaining.append({'pointer': pointer, 'occurrences': value.count(token),
                                  'counterexample': re.sub(r'sha256:[0-9a-f]+',
                                                           '<unresolved-identifier>', excerpt)})

        walk(json.loads(projected))
        observation['remaining_selectors'] = remaining
        observation['status'] = ('blocked' if remaining else
                                 'locally_bound_pending_independent_review')
        (EVIDENCE / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    print(json.dumps({'parents': len(observations), 'draft_occurrences': len(entries)}))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('artifact_root', type=Path)
    inspect(parser.parse_args().artifact_root)
