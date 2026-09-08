import pytest

from codex_harness.application.migration_ledger import reconcile
from codex_harness.domain.model import ContractError


def inventory():
    return {'revision': 'pin', 'tree': 'tree', 'entries': [
        {'path_base64': 'YS5weQ==', 'object_id': 'blob', 'kind': 'blob', 'mode': '100644', 'size': 10}]}


def test_prior_claims_and_automatic_semantic_record_do_not_certify_migration():
    result = reconcile(inventory(), {'a.py': [{'document_ref': 'existing'}]},
                       {'YS5weQ==': [{'disposition': 'semantic'}]}, [])
    row, = result['rows']
    assert row['source_read'] == 'not_attested'
    assert row['semantic_review'] == 'unreviewed'
    assert row['deployment_mapping'] == 'not_attested'
    assert result['summary']['paths_with_existing_claims'] == 1
    assert result['summary']['automatic_dispositions'] == {'semantic': 1}


@pytest.mark.parametrize('change', ['duplicate', 'unknown', 'stale'])
def test_bad_evidence_cannot_silently_drop_or_certify_paths(change):
    source = inventory()
    reviews = []
    automatic = {}
    if change == 'duplicate':
        source['entries'] *= 2
    elif change == 'unknown':
        automatic['unknown'] = []
    else:
        reviews = [{'path': 'a.py', 'revision': 'different', 'object_id': 'blob'}]
    with pytest.raises(ContractError):
        reconcile(source, {}, automatic, reviews)


def test_scoped_read_retains_remaining_gates():
    review = {'path': 'a.py', 'revision': 'pin', 'object_id': 'blob', 'source_ref': 'source',
              'analysis_ref': 'analysis', 'scope': 'Module behavior; integration remains open'}
    result = reconcile(inventory(), {}, {}, [review])
    assert result['summary']['full_source_reads_attested'] == 1
    assert result['summary']['independently_reviewed_paths'] == 0
    assert result['rows'][0]['adoption'] == 'not_attested'
