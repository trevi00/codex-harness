"""Exact, Git-owned bindings for historical bounded reader output."""
import hashlib
import json
import re
from importlib.resources import files

from codex_harness.application.artifact_query import pointer
from codex_harness.domain.model import require


def _hash(data):
    return hashlib.sha256(data).hexdigest()


class ReaderProvenance:
    def __init__(self, data):
        document = json.loads(data)
        require(set(document) == {'version', 'entries'} and document['version'] == 1,
                'Invalid reader provenance schema')
        self.entries = {}
        for entry in document['entries']:
            require(set(entry) == {'parent', 'original', 'command_hex', 'output_hex',
                                   'pointer', 'cursor', 'limit'}, 'Invalid reader binding')
            require(all(isinstance(entry[k], str) and re.fullmatch(r'sha256:[0-9a-f]{64}', entry[k])
                        for k in ('parent', 'original')), 'Invalid reader identity')
            require(all(isinstance(entry[k], str) and re.fullmatch(r'[0-9a-f]{64}', entry[k])
                        for k in ('command_hex', 'output_hex')), 'Invalid reader digest')
            require(entry['parent'] not in self.entries, 'Duplicate reader binding')
            self.entries[entry['parent']] = entry

    def project(self, path, content):
        entry = self.entries.get('sha256:' + path.stem)
        if entry is None:
            return content, set()
        require(_hash(content) == path.stem, 'Reader parent changed')
        document = json.loads(content)
        event = document['event']
        item = event['params']['item']
        require(event['method'] == 'item/completed' and item['type'] == 'commandExecution'
                and item['status'] == 'completed' and type(item['exitCode']) is int
                and item['exitCode'] == 0, 'Reader execution incomplete')
        require(_hash(item['command'].encode()) == entry['command_hex']
                and _hash(item['aggregatedOutput'].encode()) == entry['output_hex'],
                'Reader execution binding changed')
        origin = path.parent / (entry['original'][7:] + '.txt')
        require(not origin.is_symlink() and origin.resolve().parent == path.parent.resolve(),
                'Reader origin escaped store')
        data = origin.read_bytes()
        require(_hash(data) == entry['original'][7:], 'Reader origin changed')
        reproduced = pointer(entry['original'], data.decode('utf-8'), entry['pointer'],
                             entry['cursor'], entry['limit'])
        require(reproduced == item['aggregatedOutput'], 'Reader output cannot be reproduced')
        # INV-RESOURCE-001: replace only this exact output occurrence. Traverse the
        # complete original, keep other fields and independently retain live blobs.
        item['aggregatedOutput'] = entry['original']
        return json.dumps(document, ensure_ascii=False).encode(), {entry['original']}


READER_PROVENANCE = ReaderProvenance(files('codex_harness.resources').joinpath(
    'reader-output-provenance.v1.json').read_bytes())
