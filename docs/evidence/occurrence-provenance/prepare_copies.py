"""Prepare bounded review inputs. Never execute archived commands or scan archives."""

import argparse
import base64
import json
import subprocess
import zlib
from pathlib import Path

from codex_harness.adapters.historical_provenance import (
    REVISIONS,
    SOURCES,
    Corpus,
    derive,
    digest,
)

PATHS = {
    'malformed': ['docs/evidence/malformed-prefix-rework/reproduction.json',
                  'src/codex_harness/adapters/record_references.py'],
    'malformed_base': ['docs/evidence/malformed-prefix-rework/reproduction.json',
                       'src/codex_harness/adapters/record_references.py'],
    'malformed_rejected': ['src/codex_harness/adapters/record_references.py'],
    'restored': ['tests/test_reference_kinds.py'],
    'base': ['docs/evidence/reference-rework/intermediate-pytest.json',
             'docs/evidence/reference-prefix-rework/negative-control.json'],
    'rework': ['tests/test_reference_kinds.py',
               'docs/evidence/reference-rework/intermediate-pytest.json',
               'docs/evidence/reference-rework/intermediate-validation.json',
               'src/codex_harness/adapters/record_references.py'],
    'prefix': ['docs/evidence/reference-prefix-rework/negative-control.json'],
    'runner_candidate': ['tests/test_reference_kinds.py',
                         'tests/fixtures/reference_runner/original.txt',
                         'docs/evidence/python-runner-rework/negative-control.json'],
}


def pack(data):
    return base64.b64encode(zlib.compress(data, 9)).decode()


def prepare(artifact_root, output):
    document = {'version': 1, 'sources': {}, 'git_objects': {},
                'revisions': REVISIONS, 'occurrences': []}
    checkpoint = output.with_suffix('.checkpoint.json')
    for name, identifier in SOURCES.items():
        data = (artifact_root / (identifier + '.txt')).read_bytes()
        assert len(data) <= 2_000_000 and digest(data) == identifier
        document['sources'][name] = {'ref': 'sha256:' + identifier, 'data': pack(data)}
        checkpoint.write_text(json.dumps({'phase': 'sources', 'verified': list(document['sources'])}) + '\n')

    def add(oid):
        kind = subprocess.check_output(['git', 'cat-file', '-t', oid]).decode().strip()
        data = subprocess.check_output(['git', 'cat-file', kind, oid])
        document['git_objects'][oid] = {'kind': kind, 'data': pack(data)}
        return data

    for name, revision in REVISIONS.items():
        commit = add(revision)
        tree = commit.split(b'\n', 1)[0][5:].decode()
        for path in PATHS[name]:
            oid = tree
            for part in path.split('/'):
                raw = add(oid)
                children = {}
                while raw:
                    header, raw = raw.split(b'\0', 1)
                    children[header.split(b' ', 1)[1].decode()] = raw[:20].hex()
                    raw = raw[20:]
                if part not in children:
                    break
                oid = children[part]
            else:
                add(oid)
        checkpoint.write_text(json.dumps({'phase': 'git', 'revision': revision}) + '\n')
    corpus = Corpus(document)
    document['occurrences'] = derive(corpus)
    output.write_text(json.dumps(document, indent=2) + '\n')
    checkpoint.write_text(json.dumps({'phase': 'complete', 'resource_hex': digest(output.read_bytes()),
                                      'occurrences': len(document['occurrences'])}) + '\n')
    print(json.dumps({'occurrences': len(document['occurrences']), 'resource_hex': digest(output.read_bytes())}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('artifact_root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    prepare(args.artifact_root, args.output)
