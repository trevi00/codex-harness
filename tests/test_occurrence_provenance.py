import hashlib
import json
import os

import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.maintenance import ArtifactMaintenance
from codex_harness.adapters.occurrence_provenance import OccurrenceProvenance
from codex_harness.adapters.record_references import potential_references
from codex_harness.adapters.store import MemoryStore

TOKEN = 'sha256:' + '1' * 64


def fixture(extra=None):
    command = "python -c \"r='sha256:'+'1'*64; print(r)\""
    value = {'events': [{'method': 'item/completed', 'params': {
        'threadId': 'thread', 'turnId': 'turn', 'item': {
            'id': 'command', 'type': 'commandExecution', 'status': 'completed',
            'exitCode': 0, 'command': command, 'aggregatedOutput': 'é ' + TOKEN + ' ' + TOKEN}}}]}
    if extra:
        value.update(extra)
    content = json.dumps(value).encode()
    parent = 'sha256:' + hashlib.sha256(content).hexdigest()
    entry = {'parent': parent, 'origin_event': 0, 'target_event': 0, 'output_offset': 0,
             'start': 3, 'end': 74, 'namespace': 'isolated-test-token', 'hex': '1' * 64,
             'command_hex': hashlib.sha256(command.encode()).hexdigest(),
             'output_hex': hashlib.sha256(('é ' + TOKEN + ' ' + TOKEN).encode()).hexdigest(),
             'expression': "'sha256:'+'1'*64"}
    return parent, content, entry


def registry(entries, **extra):
    return OccurrenceProvenance(json.dumps({'version': 1, 'occurrences': entries, **extra}).encode())


def test_exact_occurrence_and_unannotated_equal_reference():
    parent, content, entry = fixture({'evidence_ref': TOKEN})
    projected, origins = registry([entry]).project(parent, content)
    assert json.loads(projected)['evidence_ref'] == TOKEN
    assert json.loads(projected)['events'][0]['params']['item']['aggregatedOutput'].count(TOKEN) == 1
    assert origins == {parent}
    assert potential_references(content.decode()) == {TOKEN}


@pytest.mark.parametrize('field,value', [
    ('start', 4), ('end', 75), ('origin_event', 99), ('target_event', 99),
    ('output_offset', 1), ('command_hex', '0' * 64), ('output_hex', '0' * 64),
])
def test_corrupt_bindings_fail_closed(field, value):
    parent, content, entry = fixture()
    entry[field] = value
    with pytest.raises(ValueError):
        registry([entry]).project(parent, content)


def test_stale_overlap_unknown_schema_and_namespace_rejected():
    parent, content, entry = fixture()
    with pytest.raises(ValueError):
        registry([entry]).project(parent, content + b' ')
    with pytest.raises(ValueError):
        registry([entry, entry]).project(parent, content)
    for update in ({'namespace': 'oci-image'}, {'start': True}, {'approved': True}):
        with pytest.raises(ValueError):
            registry([{**entry, **update}])
    for version in (True, '1', 2):
        with pytest.raises(ValueError):
            registry([entry], version=version)


def test_arbitrary_copied_summary_not_approved_and_revision_changes():
    parent, content, entry = fixture()
    bindings = registry([entry])
    copy = json.dumps({'summary': TOKEN}).encode()
    other = 'sha256:' + hashlib.sha256(copy).hexdigest()
    assert bindings.project(other, copy) == (copy, set())
    assert bindings.revision != registry([]).revision
    assert bindings.project(parent, content)[1] == {parent}


def test_actual_child_retained_even_with_incorrect_projection(tmp_path, monkeypatch):
    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('real child evidence', 'test')['ref']
    parent = artifacts.put(json.dumps({'evidence_ref': child}), 'test')['ref']
    orphan = artifacts.put('unreferenced control', 'test')['ref']
    for path in artifacts.root.glob('*.txt'):
        os.utime(path, (1, 1))
    with store.transaction() as tx:
        tx.put('roots', 'parent', {'ref': parent})

    class WrongProvenance:
        revision = 'wrong-reviewed-annotation'

        def project(self, ref, content):
            return b'{}', set()

    monkeypatch.setattr('codex_harness.adapters.maintenance.PROVENANCE', WrongProvenance())
    result = ArtifactMaintenance(store, artifacts).collect(apply=True)
    assert result['files'] == 1
    assert (artifacts.root / (child[7:] + '.txt')).exists()
    assert (artifacts.root / (parent[7:] + '.txt')).exists()
    assert not (artifacts.root / (orphan[7:] + '.txt')).exists()


def test_invalid_attestation_prevents_any_collection(tmp_path, monkeypatch):
    parent, content, entry = fixture()
    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    assert artifacts.put(content.decode(), 'test')['ref'] == parent
    orphan = artifacts.put('orphan', 'test')['ref']
    for path in artifacts.root.glob('*.txt'):
        os.utime(path, (1, 1))
    with store.transaction() as tx:
        tx.put('roots', 'parent', {'ref': parent})
    entry['output_hex'] = '0' * 64
    monkeypatch.setattr('codex_harness.adapters.maintenance.PROVENANCE', registry([entry]))
    with pytest.raises(ValueError):
        ArtifactMaintenance(store, artifacts).collect(apply=True)
    assert (artifacts.root / (orphan[7:] + '.txt')).exists()


def test_tombstone_fencing_uses_original_annotated_bytes(tmp_path, monkeypatch):
    parent, content, entry = fixture()
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    monkeypatch.setattr('codex_harness.adapters.maintenance.PROVENANCE', registry([entry]))
    (artifacts.root / (TOKEN[7:] + '.deleted')).write_text('collected')
    with pytest.raises(ValueError, match='dependency was collected'):
        artifacts.put(content.decode(), 'test')
    assert not (artifacts.root / (parent[7:] + '.txt')).exists()


def test_output_delta_requires_same_stream_and_complete_content_binding():
    _, content, entry = fixture()
    value = json.loads(content)
    output = value['events'][0]['params']['item']['aggregatedOutput']
    value['events'].append({'method': 'item/commandExecution/outputDelta', 'params': {
        'threadId': 'thread', 'turnId': 'turn', 'itemId': 'command', 'delta': output}})
    content = json.dumps(value).encode()
    parent = 'sha256:' + hashlib.sha256(content).hexdigest()
    entry.update(parent=parent, target_event=1)
    projected, _ = registry([entry]).project(parent, content)
    assert json.loads(projected)['events'][1]['params']['delta'].count(TOKEN) == 1
    value['events'][1]['params']['turnId'] = 'other-turn'
    content = json.dumps(value).encode()
    entry['parent'] = 'sha256:' + hashlib.sha256(content).hexdigest()
    with pytest.raises(ValueError, match='stream mismatch'):
        registry([entry]).project(entry['parent'], content)
