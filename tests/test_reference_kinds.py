import json
import time

import pytest

from codex_harness.adapters.record_references import (
    LEGACY_IMAGE_DIAGNOSTIC,
    artifact_references,
    record_references,
)

IMAGE = 'sha256:' + '1' * 64
EVIDENCE = 'sha256:' + '2' * 64


def test_nested_receipts_distinguish_images_from_evidence_without_dropping_real_edges():
    receipt = {'image': IMAGE, 'checks': {'evidence': EVIDENCE}, 'argv': [
        'docker', 'run', '--rm', '--memory', '512m', '-e', 'REFERENCE=' + EVIDENCE,
        '--entrypoint', 'codex', IMAGE, 'exec', 'Read ' + EVIDENCE]}
    nested = {'output': json.dumps({'stdout': json.dumps(receipt)})}
    assert artifact_references(json.dumps(nested)) == {EVIDENCE}
    assert artifact_references({'image': IMAGE, 'ref': IMAGE}) == {IMAGE}


def test_hook_metadata_requires_the_native_handler_shape():
    handler = {'currentHash': IMAGE, 'handlerType': 'command', 'eventName': 'sessionStart',
               'command': 'python hook.py', 'evidence_ref': EVIDENCE}
    assert artifact_references(handler) == {EVIDENCE}
    assert artifact_references({'currentHash': IMAGE}) == {IMAGE}


def test_image_identity_stdout_requires_an_exact_typed_docker_query():
    argv = ['docker', 'inspect', 'container', '--format', '{{.Image}}']
    assert artifact_references({'argv': argv, 'stdout': IMAGE + '\n'}) == set()
    assert artifact_references({'argv': ['echo', IMAGE], 'stdout': IMAGE}) == {IMAGE}
    assert artifact_references({'argv': ['docker', 'image', 'inspect', 'image', '--format', EVIDENCE],
                                'stdout': EVIDENCE}) == {EVIDENCE}


@pytest.mark.parametrize('body', [IMAGE, 'Reference ' + IMAGE,
    '{"image":"' + IMAGE + '","image":"' + EVIDENCE + '"}',
    {'argv': ['docker', 'run', '--unknown-flag', IMAGE]},
    {'image': IMAGE, IMAGE: {'ref': IMAGE}},
])
def test_ambiguous_syntax_and_explicit_references_remain_conservative(body):
    assert IMAGE in artifact_references(body)


def test_bucket_and_record_identity_are_always_artifact_edges():
    assert record_references(IMAGE, EVIDENCE, {'image': IMAGE}) == {IMAGE, EVIDENCE}
    assert artifact_references({'stdout': json.dumps({'ref': EVIDENCE})}) == {EVIDENCE}


def test_clipped_diagnostic_json_excludes_only_complete_typed_image_tokens():
    fragment = 'integrity True\n{"candidate":{},"image":"' + IMAGE + '","ref":"' + EVIDENCE + '","rest":'
    assert artifact_references({'aggregatedOutput': fragment}) == {IMAGE, EVIDENCE}
    assert artifact_references(fragment) == {IMAGE, EVIDENCE}
    assert artifact_references({'stdout': 'image ' + IMAGE + ' ref ' + EVIDENCE}) == {IMAGE, EVIDENCE}
    assert artifact_references({'stdout': '{"image":"' + IMAGE}) == {IMAGE}
    assert artifact_references({'image': IMAGE}) == {IMAGE}
    assert artifact_references({'stdout': '{"image":"' + IMAGE + '","rest":'}) == {IMAGE}


def test_legacy_image_diagnostic_does_not_exempt_missing_evidence():
    diagnostic = {'root_cause': LEGACY_IMAGE_DIAGNOSTIC, 'status': 'collection_deferred',
                  'missing_digest': IMAGE, 'evidence_parent_refs': [EVIDENCE]}
    assert artifact_references(diagnostic) == {EVIDENCE}
    diagnostic['root_cause'] = 'Missing actual artifact'
    assert artifact_references(diagnostic) == {IMAGE, EVIDENCE}


def test_escaped_diagnostic_near_miss_does_not_cause_quadratic_scanning():
    diagnostic = '\\' * 50000 + '"not_an_image":"' + EVIDENCE + '"'
    started = time.monotonic()
    assert artifact_references({'stdout': diagnostic}) == {EVIDENCE}
    assert time.monotonic() - started < 1


def test_lockfile_download_integrity_is_not_an_artifact_edge():
    line = '{ url = "https://files.pythonhosted.org/package.whl", hash = "' + IMAGE + '", size = 20 },'
    lockfile = 'version = 1\n[[package]]\nwheels = [\n' + line + '\n]\n# evidence ' + IMAGE + '\n'
    assert artifact_references(line) == set()
    assert artifact_references({'lines': [line]}) == set()
    assert artifact_references(lockfile) == {IMAGE}
    assert artifact_references({'url': 'https://example.com/file', 'hash': IMAGE, 'ref': EVIDENCE}) == {EVIDENCE}
    assert artifact_references({'hash': IMAGE}) == {IMAGE}
    assert artifact_references('{ hash = "' + IMAGE + '", ref = "' + EVIDENCE + '" },') == {IMAGE, EVIDENCE}


@pytest.mark.parametrize('url', ['https://[broken', 'file:///tmp/package', '', 'https:///missing-host'])
def test_invalid_download_metadata_retains_references(url):
    assert artifact_references({'url': url, 'hash': IMAGE}) == {IMAGE}
    line = '{ url = "' + url + '", hash = "' + IMAGE + '" },'
    assert artifact_references(line) == {IMAGE}


def test_release_merge_result_and_numbered_lockfile_output():
    result = {'image': IMAGE, 'merge': {'merged': True, 'revision': 'a' * 40},
              'evidence_ref': EVIDENCE}
    assert artifact_references({'result': result}) == {EVIDENCE}
    assert artifact_references({'image': IMAGE, 'merge': 'unknown'}) == {IMAGE}
    line = '40:sdist = { url = "https://example.com/file", hash = "' + IMAGE + '" }'
    assert artifact_references({'delta': line}) == set()
    assert artifact_references({'delta': line + ' # evidence ' + EVIDENCE}) == {EVIDENCE}
    assert artifact_references({'image': IMAGE, 'command': ['docker', 'run', '--rm', IMAGE],
                                'evidence_ref': EVIDENCE}) == {EVIDENCE}


def test_buildkit_progress_only_excludes_complete_identity_lines():
    lines = ['#21 exporting manifest ' + IMAGE + ' done',
             '#21 exporting config ' + IMAGE + ' 0.0s done',
             '#7 [stage-1 1/11] FROM docker.io/library/python:3.13@' + IMAGE,
             '#7 resolve docker.io/library/python:3.13@' + IMAGE + ' 0.0s done']
    assert artifact_references('\n'.join(lines)) == set()
    assert artifact_references(lines[0] + ' evidence ' + EVIDENCE) == {IMAGE, EVIDENCE}
    assert artifact_references('exporting manifest ' + IMAGE) == {IMAGE}


def test_native_trust_map_and_explicit_image_prose_keep_evidence():
    trust = {'/<session-flags>/config.toml:session_start:0:0': {
        'enabled': True, 'trusted_hash': IMAGE, 'evidence_ref': EVIDENCE}}
    assert artifact_references(trust) == {EVIDENCE}
    assert artifact_references({'trusted_hash': IMAGE}) == {IMAGE}
    assert artifact_references('Verified immutable Docker image ' + IMAGE + '; evidence ' + IMAGE) == {IMAGE}
    assert artifact_references('Verified immutable Docker image ' + IMAGE) == set()


def test_deep_execution_envelopes_retain_typed_receipt_semantics():
    body = {'handlerType': 'command', 'eventName': 'sessionStart', 'command': 'python hook.py',
            'currentHash': IMAGE, 'ref': EVIDENCE}
    for _ in range(40):
        body = {'event': [body]}
    assert artifact_references(json.dumps(body)) == {EVIDENCE}


def test_pinned_upstream_code_is_inert_and_unpinned_sources_remain_conservative():
    source = 'https://github.com/example/repo/blob/' + 'a' * 40 + '/tests/test_example.py'
    body = 'expected_digest = "' + EVIDENCE + '"'
    assert artifact_references(body, source=source) == set()
    assert artifact_references(body, source=source.replace('a' * 40, 'main')) == {EVIDENCE}
    assert artifact_references(body, source='task:implementation') == {EVIDENCE}


def test_output_frames_reassemble_receipts_and_split_evidence_handles():
    def frame(item, text):
        return {'method': 'item/commandExecution/outputDelta',
                'params': {'threadId': 'thread', 'turnId': 'turn', 'itemId': item, 'delta': text}}
    receipt = json.dumps({'candidate': {}, 'image': IMAGE, 'ref': EVIDENCE})
    split = receipt.index(EVIDENCE) + 30
    events = [frame('one', receipt[:split]), frame('two', 'evidence ' + IMAGE),
              frame('one', receipt[split:])]
    completed = {'method': 'item/completed', 'params': {'threadId': 'thread', 'turnId': 'turn',
        'item': {'id': 'one', 'type': 'commandExecution', 'aggregatedOutput': receipt}}}
    events.append(completed)
    assert artifact_references({'events': events}) == {IMAGE, EVIDENCE}
    assert artifact_references({'events': [events[0], events[2], completed]}) == {EVIDENCE}


def test_unverified_output_gaps_never_fabricate_a_joined_reference():
    events = [{'method': 'item/commandExecution/outputDelta', 'params': {
        'threadId': 'thread', 'turnId': 'turn', 'itemId': 'one', 'delta': value}}
        for value in ['sha256:' + '1' * 32, '2' * 32]]
    assert artifact_references({'events': events}) == set()
    assert artifact_references(IMAGE + 'abc') == set()


def test_completed_output_corroborates_gapped_deltas_without_joining_them():
    body = 'immutable Docker image ' + IMAGE + '\nreceipt ' + EVIDENCE
    fragment = 'cker image ' + IMAGE
    event = {'method': 'item/commandExecution/outputDelta', 'params': {
        'threadId': 'thread', 'turnId': 'turn', 'itemId': 'one', 'delta': fragment}}
    completed = {'method': 'item/completed', 'params': {'threadId': 'thread', 'turnId': 'turn',
        'item': {'id': 'one', 'type': 'commandExecution', 'aggregatedOutput': body}}}
    assert artifact_references({'events': [event]}) == {IMAGE}
    assert artifact_references({'events': [event, completed]}) == {EVIDENCE}
    event['params']['delta'] = 'unmatched evidence ' + IMAGE
    assert artifact_references({'events': [event, completed]}) == {IMAGE, EVIDENCE}


def test_partial_docker_word_needs_complete_local_identity_and_output_context():
    fragment = {'stdout': 'cker image ' + IMAGE + ', remaining output ' + EVIDENCE}
    assert artifact_references(fragment) == {IMAGE, EVIDENCE}
    assert artifact_references({'fragment': fragment, 'description': 'immutable Docker image ' + IMAGE}) == {IMAGE, EVIDENCE}
    assert artifact_references({'fragment': fragment, 'description': 'immutable Docker image ' + IMAGE,
                                'evidence_ref': IMAGE}) == {IMAGE, EVIDENCE}
    assert artifact_references({'fragment': 'cker image ' + IMAGE,
                                'description': 'immutable Docker image ' + IMAGE}) == {IMAGE}
    clipped = {'stdout': ' ' + IMAGE + ', then the real CLI file-task canary was run by that immutable ID.'}
    assert artifact_references(clipped) == {IMAGE}
    assert artifact_references({'fragment': clipped, 'description': 'immutable Docker image ' + IMAGE}) == {IMAGE}
    assert artifact_references({'fragment': clipped, 'description': 'immutable Docker image ' + IMAGE,
                                'evidence_ref': IMAGE}) == {IMAGE}


def test_clipped_nested_hook_objects_require_complete_native_shape():
    hook = {'command': 'python hook.py', 'handlerType': 'command', 'eventName': 'sessionStart',
            'currentHash': IMAGE, 'evidence_ref': EVIDENCE}
    escaped = json.dumps(json.dumps(hook))[1:-1]
    assert artifact_references('clipped ' + escaped + ' remainder') == {EVIDENCE}
    assert artifact_references('clipped ' + escaped[:-1]) == {IMAGE, EVIDENCE}
    config = 'hooks={hook_state={"/<session-flags>/config.toml:session_start:0:0"={enabled=true,trusted_hash="' + IMAGE + '"}}}'
    assert artifact_references(config) == set()


def test_escaped_download_metadata_in_diagnostic_source_copy():
    leaf = '{ url = "https://example.com/pkg.whl", hash = "' + IMAGE + '", ref = "' + EVIDENCE + '" }'
    for _ in range(3):
        leaf = json.dumps(leaf)[1:-1]
    assert artifact_references('partial copy ' + leaf + ' remainder') == {EVIDENCE}
    assert artifact_references('partial copy ' + leaf[:-1]) == {IMAGE, EVIDENCE}


def test_spec_revision_and_named_handler_identity_are_not_artifact_addresses():
    assert artifact_references({'revision': 'spec-' + IMAGE, 'evidence_ref': EVIDENCE}) == {EVIDENCE}
    assert artifact_references('trusted handler hash:\n+ `' + IMAGE + '`. Evidence ' + EVIDENCE) == {EVIDENCE}
    assert artifact_references('handler evidence ' + IMAGE) == {IMAGE}


def test_complete_escaped_docker_arrays_keep_command_arguments():
    argv = json.dumps(['docker', 'run', '--rm', '--entrypoint', 'codex', IMAGE, 'exec', EVIDENCE], indent=2)
    assert artifact_references('heading\n' + argv + '\nfinished') == {EVIDENCE}
    escaped = json.dumps(json.dumps(argv))[1:-1]
    assert artifact_references('clipped ' + escaped) == {EVIDENCE}
    assert artifact_references(argv[:-1]) == {IMAGE, EVIDENCE}


def test_snapshot_cache_keys_include_complete_mutable_record_contents():
    cache = {}
    record = {'id': 'task', 'message': {'ref': EVIDENCE}, 'status': 'pending'}
    assert artifact_references(record, cache=cache) == {EVIDENCE}
    assert artifact_references(record, cache=cache) == {EVIDENCE}
    assert len(cache) == 1
    record['message']['ref'] = IMAGE
    assert artifact_references(record, cache=cache) == {IMAGE}
    assert len(cache) == 2


def test_source_metadata_is_validated_before_namespace_classification(tmp_path):
    from codex_harness.adapters.artifacts import FileArtifacts
    from codex_harness.adapters.maintenance import ArtifactMaintenance
    from codex_harness.domain.model import ContractError

    artifacts = FileArtifacts(str(tmp_path))
    source = 'https://github.com/example/repo/blob/' + 'a' * 40 + '/fixture.py'
    ref = artifacts.put(EVIDENCE, source)['ref']
    path = tmp_path / (ref[7:] + '.txt')
    assert ArtifactMaintenance._dependencies(path, path.read_bytes()) == set()
    meta = json.loads(path.with_suffix('.json').read_text())
    meta['bytes'] += 1
    path.with_suffix('.json').write_text(json.dumps(meta))
    with pytest.raises(ContractError, match='metadata mismatch'):
        ArtifactMaintenance._dependencies(path, path.read_bytes())


def test_clipped_identity_tokens_bind_only_to_complete_declarations_in_same_artifact():
    fragment = {'stdout': 'clipped "currentHash":"' + IMAGE + '", rest'}
    assert artifact_references(fragment) == {IMAGE}
    declaration = {'handlerType': 'command', 'command': 'python hook.py',
                   'eventName': 'sessionStart', 'currentHash': IMAGE}
    assert artifact_references({'declaration': declaration, 'fragment': fragment}) == {IMAGE}
    assert artifact_references({'declaration': declaration, 'fragment': fragment,
                                'evidence_ref': IMAGE}) == {IMAGE}
    image_fragment = {'stdout': 'clipped "image":"' + IMAGE + '", rest'}
    assert artifact_references(image_fragment) == {IMAGE}
    assert artifact_references({'receipt': {'candidate': {}, 'image': IMAGE},
                                'fragment': image_fragment, 'ref': EVIDENCE}) == {IMAGE, EVIDENCE}
    assert artifact_references({'stdout': 'actual runner image: ' + IMAGE}) == set()
    assert artifact_references({'stdout': 'actual runner image: ' + IMAGE + ' ref ' + EVIDENCE}) == {IMAGE, EVIDENCE}


def test_measurement_cache_ignores_only_non_reference_observation_timestamps(tmp_path):
    from codex_harness.adapters.artifacts import FileArtifacts
    from codex_harness.adapters.maintenance import ArtifactMaintenance

    artifacts, cache = FileArtifacts(str(tmp_path)), {}
    for at, expected in [('2026-09-09T01:00:00+00:00', EVIDENCE),
                         ('2026-09-09T01:00:01+00:00', EVIDENCE),
                         ('2026-09-09T01:00:02+00:00', IMAGE)]:
        body = json.dumps({'observed_at': at, 'ref': expected})
        ref = artifacts.put(body, 'conductor-measurements.v1')['ref']
        path = tmp_path / (ref[7:] + '.txt')
        assert ArtifactMaintenance._dependencies(path, path.read_bytes(), cache) == {expected}
    assert len(cache) == 2


def test_migration_claims_keep_retained_evidence_and_preserve_unavailability_as_a_finding():
    claim = {'document': 'docs/audit.md', 'document_ref': EVIDENCE,
             'origin': 'Retained working-tree text; not a Git-reviewed attestation',
             'retained_evidence_refs': [EVIDENCE], 'unavailable_evidence_handles': [IMAGE]}
    assert artifact_references(claim) == {EVIDENCE}
    claim['retained_evidence_refs'].append(IMAGE)
    assert artifact_references(claim) == {IMAGE, EVIDENCE}
    assert artifact_references({'unavailable_evidence_handles': [IMAGE]}) == {IMAGE}
    assert artifact_references({'service': 'conductor', 'name': 'container', 'state': 'running',
                                'image': IMAGE, 'evidence_ref': EVIDENCE}) == {EVIDENCE}
    assert artifact_references({'service': 'conductor', 'state': 'running', 'cli_exit_code': 0,
                                'cli_version': 'codex-cli 0.153.4', 'image': IMAGE,
                                'evidence_ref': EVIDENCE}) == {EVIDENCE}


@pytest.mark.parametrize('prefix', ['', 'log [unfinished ', '[' * 20, 'header { unfinished '])
@pytest.mark.parametrize('ending', ['}', ', "truncated":', ', "nested": ['])
def test_duplicate_keys_never_gain_metadata_semantics_after_invalid_prefix_or_truncation(prefix, ending):
    body = prefix + '{"candidate":{},"image":"' + EVIDENCE + '","image":"unknown"' + ending
    assert EVIDENCE in artifact_references({'stdout': body})
    escaped = body.replace('sha256:', r'\u0073ha256:')
    assert EVIDENCE in artifact_references({'stdout': escaped})


def test_retained_migration_markdown_image_label_is_source_scoped():
    body = 'Receipt: `' + EVIDENCE + '`.\nImage: `' + IMAGE + '`.\n'
    assert artifact_references(body, source='migration-claim-document') == {EVIDENCE}
    assert artifact_references(body) == {IMAGE, EVIDENCE}
    assert artifact_references(body + 'Evidence: ' + IMAGE,
                               source='migration-claim-document') == {IMAGE, EVIDENCE}
    assert artifact_references('Image: `' + IMAGE + '`. ref ' + EVIDENCE,
                               source='migration-claim-document') == {IMAGE, EVIDENCE}


@pytest.mark.parametrize('wrapper', ['plain', 'heading', 'escaped', 'nested', 'multiline', 'prefix_argv'])
@pytest.mark.parametrize('field', ['stdout', 'stderr', 'aggregatedOutput', 'output', 'delta'])
def test_duplicate_key_receipts_never_reach_typed_fragment_exclusion(wrapper, field):
    body = '{"candidate":{},"image":"' + IMAGE + '","image":"unknown"}'
    if wrapper == 'prefix_argv':
        body = json.dumps(['docker', 'run', IMAGE]) + '\n' + body
    elif wrapper == 'heading':
        body = 'receipt follows\n' + body
    elif wrapper == 'escaped':
        body = json.dumps(body)[1:-1]
    elif wrapper == 'nested':
        body = '{"receipt":' + body + '}'
    elif wrapper == 'multiline':
        body = body.replace(',', ',\n')
    assert artifact_references({field: body, 'declaration': {'candidate': {}, 'image': IMAGE}}) == {IMAGE}


def test_duplicate_keys_preserve_escaped_reference_scalars():
    body = '{"candidate":{},"image":"' + IMAGE.replace('s', r'\u0073') + '","image":"unknown"}'
    assert artifact_references({'stdout': body}) == {IMAGE}


@pytest.mark.parametrize('command', [['docker', 'inspect'], ['docker', 'image', 'inspect']])
@pytest.mark.parametrize('options', [
    ['--unknown'], ['--format'], ['--type'], ['--type', 'unknown'],
    ['--format', '{{.Image}}'], ['-f', '{{.Id}}'], ['--unknown=value'], [None],
])
def test_ambiguous_docker_inspection_keeps_operands_and_stdout(command, options):
    argv = command + [IMAGE, '--format', '{{.Id}}'] + options
    assert artifact_references({'argv': argv, 'stdout': EVIDENCE}) == {IMAGE, EVIDENCE}


RUNNER_SOURCE = 'baldrix-budget-probe-runner'


def test_original_python_runner_bytes_are_classified_without_execution():
    import hashlib
    from pathlib import Path

    body = (Path(__file__).parent / 'fixtures/reference_runner/original.txt').read_bytes()
    assert hashlib.sha256(body).hexdigest() == 'b967dca2a7a4cf978c06c0f08198ac4677b4fa28fa3e3d20a0da2d8abbf85855'
    assert artifact_references(body.decode(), source=RUNNER_SOURCE) == set()
    assert artifact_references(body.decode()) == {
        'sha256:a23534401b82ff6075822d9b111f5f78f5a7f518b0a9d30fbb111611cd6988a0'}


def test_python_runner_literal_operand_and_unicode_byte_positions():
    body = ("한글 = 'é'; argv = ['docker', 'run', '--mount', "
            "f'type=bind,source={folder}', '" + IMAGE + "', '" + EVIDENCE + "']\n")
    assert artifact_references(body, source=RUNNER_SOURCE) == {EVIDENCE}
    assert artifact_references(body.replace('\n', '\r\n'), source=RUNNER_SOURCE) == {EVIDENCE}
    assert artifact_references('# prefix\r' + body, source=RUNNER_SOURCE) == {EVIDENCE}
    assert artifact_references(body) == {IMAGE, EVIDENCE}
    assert artifact_references(body, source=RUNNER_SOURCE + '-unknown') == {IMAGE, EVIDENCE}


@pytest.mark.parametrize('body', [
    "argv = ['docker', 'run', '" + IMAGE + "'",
    "argv = ['docker', 'run', '" + IMAGE + "']\ninvalid(",
    "argv = ['docker', 'run', '--unknown', 'value', '" + IMAGE + "']",
    "argv = ['docker', 'run', image, '" + IMAGE + "']",
    "argv = ['docker', 'run', *options, '" + IMAGE + "']",
    "argv = ['docker', 'run', '--mount', *mounts, '" + IMAGE + "']",
    "# argv = [\"docker\", \"run\", \"" + IMAGE + "\"]",
    "argv = ['docker', 'run', ('sha256:' # " + EVIDENCE + "\n'" + '1' * 64 + "')]",
    "argv = ['docker', 'run', ('sha256:'\n    '' # " + EVIDENCE + "\n  '" + '1' * 64 + "')]",
])
def test_python_runner_uncertain_shapes_retain_raw_evidence(body):
    expected = {ref for ref in (IMAGE, EVIDENCE) if ref in body}
    assert artifact_references(body, source=RUNNER_SOURCE) == expected


@pytest.mark.parametrize('elsewhere', [
    "evidence = '" + IMAGE + "'",
    "# immutable Docker image " + IMAGE,
    '# ["docker", "run", "' + IMAGE + '"]',
    'receipt = {"candidate": {}, "image": "' + IMAGE + '"}',
    "argv2 = ['docker', 'run', '--env', '" + IMAGE + "', 'plain-image']",
])
def test_python_runner_same_identity_elsewhere_is_retained(elsewhere):
    body = "argv = ['docker', 'run', '" + IMAGE + "']\n" + elsewhere
    assert artifact_references(body, source=RUNNER_SOURCE) == {IMAGE}
