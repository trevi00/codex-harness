"""Reconcile path evidence without turning mentions or task success into adoption."""
import base64
from collections import Counter

from codex_harness.domain.model import require


def reconcile(inventory, claims, automatic, reviews):
    entries = inventory['entries']
    paths = {entry['path_base64']: entry for entry in entries}
    require(len(paths) == len(entries), 'Duplicate inventory path')
    require(set(automatic) <= set(paths), 'Automatic record outside pinned inventory')
    review_map = {}
    for review in reviews:
        key = base64.b64encode(review['path'].encode('utf-8')).decode('ascii')
        require(key in paths and key not in review_map, 'Unknown or duplicate review path')
        require(review['revision'] == inventory['revision']
                and review['object_id'] == paths[key]['object_id'], 'Stale source review')
        require(review['source_ref'] and review['analysis_ref'] and review['scope'],
                'Review evidence incomplete')
        review_map[key] = review
    rows = []
    for key, entry in sorted(paths.items()):
        path = base64.b64decode(key, validate=True).decode('utf-8', errors='backslashreplace')
        review = review_map.get(key)
        rows.append({**entry, 'path': path,
            'source_read': 'complete' if review else 'not_attested',
            'semantic_review': 'scoped_pending_independent_review' if review else 'unreviewed',
            'review': review,
            'existing_claims': claims.get(path, []),
            'automatic_records': automatic.get(key, []),
            # INV-MIGRATION-001: none of these observations grants adoption or deployment authority.
            'adoption': 'not_attested', 'implementation_mapping': 'not_attested',
            'deployment_mapping': 'not_attested'})
    return {'schema': 'migration-path-ledger.v1', 'revision': inventory['revision'],
            'tree': inventory['tree'], 'rows': rows,
            'summary': {'paths': len(rows), 'full_source_reads_attested': len(review_map),
                'paths_with_existing_claims': sum(bool(r['existing_claims']) for r in rows),
                'automatic_dispositions': dict(Counter(
                    record['disposition'] for r in rows for record in r['automatic_records'])),
                'independently_reviewed_paths': 0, 'path_deployment_attestations': 0},
            'limitations': ['Document mentions are reconciliation candidates, not semantic review.',
                'Existing component deployment receipts do not certify every upstream path.',
                'Automatic dispositions are reported verbatim without revalidation.',
                'Zero attestations means missing path-level proof, not absent component implementation.']}
