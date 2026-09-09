import hashlib
import json

import pytest

from codex_harness.adapters.reader_provenance import ReaderProvenance
from codex_harness.adapters.record_references import artifact_references
from codex_harness.application.artifact_query import pointer
from codex_harness.domain.model import ContractError


def fixture(tmp_path):
    token = 'sha256:' + 'a' * 64
    source = json.dumps({'lines': ['{ url = "https://example.com/a", hash = "' + token + '" },'] * 30})
    ref = 'sha256:' + hashlib.sha256(source.encode()).hexdigest()
    origin = tmp_path / (ref[7:] + '.txt')
    origin.write_bytes(source.encode())
    output = pointer(ref, source, '', 0, 1000)
    command = 'authenticated historical reader command'
    doc = {'event': {'method': 'item/completed', 'params': {'item': {
        'type': 'commandExecution', 'status': 'completed', 'exitCode': 0,
        'command': command, 'aggregatedOutput': output}}}, 'evidence_ref': token}
    body = json.dumps(doc).encode()
    parent = 'sha256:' + hashlib.sha256(body).hexdigest()
    path = tmp_path / (parent[7:] + '.txt')
    path.write_bytes(body)
    entry = {'parent': parent, 'original': ref, 'command_hex': hashlib.sha256(command.encode()).hexdigest(),
             'output_hex': hashlib.sha256(output.encode()).hexdigest(), 'pointer': '', 'cursor': 0, 'limit': 1000}
    proof = ReaderProvenance(json.dumps({'version': 1, 'entries': [entry]}))
    return proof, path, body, origin, ref, token


def test_exact_output_uses_complete_original_and_keeps_other_occurrences(tmp_path):
    proof, path, body, origin, ref, token = fixture(tmp_path)
    projected, roots = proof.project(path, body)
    assert roots == {ref}
    assert artifact_references(projected.decode()) == {ref, token}
    assert artifact_references(origin.read_text()) == set()
    assert path.read_bytes() == body


@pytest.mark.parametrize('kind', ['missing', 'corrupt', 'parent', 'output', 'command'])
def test_invalid_provenance_cannot_remove_edges(tmp_path, kind):
    proof, path, body, origin, ref, token = fixture(tmp_path)
    if kind == 'missing':
        origin.unlink()
    elif kind == 'corrupt':
        origin.write_bytes(b'corrupt')
    elif kind == 'parent':
        body += b' '
    else:
        proof.entries['sha256:' + path.stem][kind + '_hex'] = '0' * 64
    with pytest.raises((ContractError, FileNotFoundError)):
        proof.project(path, body)


def test_unknown_parent_retains_raw_output(tmp_path):
    proof, path, body, origin, ref, token = fixture(tmp_path)
    proof.entries.clear()
    assert proof.project(path, body) == (body, set())
