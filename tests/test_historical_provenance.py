import base64
import copy
import json
import re
import zlib
from importlib.resources import files
from pathlib import Path

import pytest

from codex_harness.adapters.historical_provenance import (
    CombinedProvenance,
    Corpus,
    HistoricalCopies,
    derive_malformed,
    digest,
    unpack,
)
from codex_harness.adapters.occurrence_provenance import OccurrenceProvenance
from codex_harness.adapters.record_references import potential_references


@pytest.fixture(scope='module')
def document():
    return json.loads(files('codex_harness.resources').joinpath('occurrence-copies.v1.json').read_bytes())


def registry(document):
    return HistoricalCopies(json.dumps(document).encode())


@pytest.fixture(scope='module')
def copies(document):
    return registry(document)


def test_all_seven_original_parents_are_bound_with_origin_dependencies(document, copies):
    original = OccurrenceProvenance(files('codex_harness.resources').joinpath(
        'occurrence-provenance.v1.json').read_bytes())
    combined = CombinedProvenance(original, copies)
    parents = {e['parent'] for e in document['occurrences']}
    assert len(parents) == 8
    assert len(document['occurrences']) == 30
    for source in document['sources'].values():
        if source['ref'] not in parents:
            continue
        raw = unpack(source['data'])
        projected, origins = combined.project(source['ref'], raw)
        entries = [e for e in document['occurrences'] if e['parent'] == source['ref']]
        tokens = {'sha256:' + e['identifier']['hex'] for e in entries}
        for token in tokens:
            assert token.encode() in raw
            assert token not in projected.decode()
        assert {r for e in entries for r in e['origins']} <= origins
        # Original-byte live-edge retention/fencing still sees each token.
        assert tokens <= potential_references(raw.decode())


@pytest.mark.parametrize('mutation', ['interval', 'selector', 'origin', 'duplicate', 'version',
                                      'bool_version', 'unknown', 'git', 'source', 'swapped',
                                      'boolean_receipt', 'float_interval'])
def test_corrupt_forged_swapped_and_unknown_proofs_rejected(document, mutation):
    value = copy.deepcopy(document)
    if mutation == 'interval':
        value['occurrences'][0]['start'] += 1
    elif mutation == 'selector':
        value['occurrences'][0]['selector_hex'] = '0' * 64
    elif mutation == 'origin':
        value['occurrences'][0]['origins'] = []
    elif mutation == 'duplicate':
        value['occurrences'].append(value['occurrences'][0])
    elif mutation == 'version':
        value['version'] = 2
    elif mutation == 'bool_version':
        value['version'] = True
    elif mutation == 'boolean_receipt':
        receipt = next(b for b in value['occurrences'][0]['bindings'] if 'exit_code' in b)
        receipt['exit_code'] = False
    elif mutation == 'float_interval':
        value['occurrences'][0]['start'] = float(value['occurrences'][0]['start'])
    elif mutation == 'unknown':
        value['approved'] = True
    elif mutation == 'git':
        key = next(iter(value['git_objects']))
        value['git_objects'][key]['data'] = base64.b64encode(zlib.compress(b'forged')).decode()
    elif mutation == 'source':
        value['sources']['runner']['data'] = base64.b64encode(zlib.compress(b'forged')).decode()
    else:
        value['revisions']['rework'], value['revisions']['prefix'] = (
            value['revisions']['prefix'], value['revisions']['rework'])
    with pytest.raises((ValueError, KeyError)):
        registry(value)


def test_digest_rebinding_cannot_approve_changed_synthetic_program(document):
    value = copy.deepcopy(document)
    source = value['sources']['loop_execution']
    raw = unpack(source['data']).replace(b"r = 'sha256:' + 'a'*64", b"r = 'sha256:' + 'b'*64")
    assert raw != unpack(source['data'])
    source.update(ref='sha256:' + digest(raw), data=base64.b64encode(zlib.compress(raw)).decode())
    with pytest.raises(ValueError, match='outside the reviewed catalogue'):
        registry(value)


def test_stale_parent_and_arbitrary_equal_copy_are_not_approved(document, copies):
    source = document['sources']['loop_execution']
    raw = unpack(source['data'])
    with pytest.raises(ValueError, match='Stale historical copy parent'):
        copies.project(source['ref'], raw + b' ', raw + b' ')
    copied = json.dumps({'summary': 'sha256:' + 'a' * 64}).encode()
    assert copies.project('sha256:' + digest(copied), copied, copied) == (copied, set())


def test_reviewed_resource_revision_is_part_of_combined_cache_identity(document, copies):
    original = OccurrenceProvenance(b'{"version":1,"occurrences":[]}')
    combined = CombinedProvenance(original, copies)
    # Even formatting changes bind a distinct immutable source snapshot.
    other = HistoricalCopies(json.dumps(document, indent=2).encode())
    assert combined.revision != CombinedProvenance(original, other).revision


def test_composition_rejects_an_overlap_with_previous_projection(document, copies):
    source = document['sources']['loop_execution']
    raw = unpack(source['data'])
    projected = raw.replace(('sha256:' + 'a' * 64).encode(), b'OTHER_TOKEN')
    with pytest.raises(ValueError, match='Overlapping provenance versions'):
        copies.project(source['ref'], raw, projected)


def test_catalogue_covers_exact_original_blocked_selectors(document):
    observations = json.loads(Path('docs/evidence/occurrence-provenance/observations.json').read_text())
    blocked = [row for row in observations if row['status'] == 'blocked']
    sources = {source['ref']: unpack(source['data']) for source in document['sources'].values()}
    new_parent = document['sources']['malformed_diff']['ref']
    assert {row['parent'] for row in blocked} == {
        e['parent'] for e in document['occurrences'] if e['parent'] != new_parent}
    for row in blocked:
        token = ('sha256:' + row['identifier']['hex']).encode()
        raw = sources[row['parent']]
        assert len(raw) == row['bytes']
        assert [m.start() for m in re.finditer(re.escape(token), raw)] == row['raw_occurrences']
        entries = [e for e in document['occurrences'] if e['parent'] == row['parent']]
        assert len(entries) + row['attested_occurrences'] == len(row['raw_occurrences'])
        assert {e['selector'] for e in entries} == {
            selector['pointer'] for selector in row['remaining_selectors']}
        for selector in row['remaining_selectors']:
            assert sum(e['selector'] == selector['pointer'] for e in entries) == selector['occurrences']
        assert all(origin in sources for entry in entries for origin in entry['origins'])


def test_equal_valued_explicit_handle_remains_mandatory(document, copies):
    # INV-RESOURCE-001: even within an authenticated parent, an unannotated
    # handle cannot inherit a classification from the adjacent identical token.
    source = document['sources']['loop_execution']
    raw = unpack(source['data'])
    value = json.loads(raw)
    token = 'sha256:' + 'a' * 64
    value['evidence_ref'] = token
    content = json.dumps(value).encode()
    # Exercise the projection boundary with an intentionally wrong catalogue
    # association; runtime callers cannot mutate the packaged catalogue.
    forged = copy.copy(copies)
    forged._entries = {'sha256:' + digest(content): copies._entries[source['ref']]}
    projected, _ = forged.project('sha256:' + digest(content), content, content)
    assert json.loads(projected)['evidence_ref'] == token
    assert token in potential_references(projected.decode())


def test_new_production_diff_is_bound_to_exact_reproduction_bytes(document, copies):
    source = document['sources']['malformed_diff']
    raw = unpack(source['data'])
    entries = copies._entries[source['ref']]
    assert len(entries) == 5
    assert {e['selector'] for e in entries} == {'/independent_diff/diff'}
    projected, origins = copies.project(source['ref'], raw, raw)
    token = 'sha256:' + entries[0]['identifier']['hex']
    assert token in potential_references(raw.decode())
    assert token not in potential_references(projected.decode())
    assert origins == {source['ref'], document['sources']['malformed_execution']['ref']}
    # An equal-valued real handle outside the proven diff remains a dependency.
    value = json.loads(raw)
    value['evidence_ref'] = token
    other = json.dumps(value).encode()
    forged = copy.copy(copies)
    forged._entries = {'sha256:' + digest(other): entries}
    projected, _ = forged.project('sha256:' + digest(other), other, other)
    assert token in potential_references(projected.decode())


@pytest.mark.parametrize('mutation', ['base', 'tree', 'revision', 'diff', 'command', 'output', 'failed'])
def test_new_diff_derivation_rejects_swapped_or_unproven_sources(document, mutation):
    # Deliberately bypass outer source authentication to test the inner proof too.
    corpus = Corpus(document)
    name = 'malformed_diff' if mutation in {'base', 'tree', 'revision', 'diff'} else 'malformed_execution'
    value = corpus.document(name)
    if mutation in {'base', 'tree', 'revision'}:
        value['candidate'][mutation] = '0' * 40
        value['independent_diff'][mutation] = '0' * 40
    elif mutation == 'diff':
        value['independent_diff']['diff'] = value['independent_diff']['diff'].replace(
            '+  "input":', '+  "copied_input":')
    elif mutation == 'command':
        value['events'][821]['params']['item']['command'] += ' '
        # Change program bytes, not ignorable shell whitespace.
        value['events'][821]['params']['item']['command'] = value['events'][821]['params']['item'][
            'command'].replace("'1' * 64", "'2' * 64")
    elif mutation == 'output':
        value['events'][894]['params']['item']['aggregatedOutput'] = ''
    else:
        value['events'][821]['params']['item']['exitCode'] = 1
    corpus.raw[name] = json.dumps(value).encode()
    with pytest.raises(ValueError):
        derive_malformed(corpus)
