"""Build a pinned Baldrix reconciliation snapshot and a spreadsheet from retained evidence."""
import argparse
import base64
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.application.migration_ledger import reconcile
from codex_harness.bootstrap import build
from codex_harness.domain.model import require, utcnow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--reviews', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    artifacts = FileArtifacts(root / '.runtime/artifacts')
    catalog = json.loads((root / 'docs/migration-sequence.json').read_text('utf-8'))['sequence'][0]
    inventory = artifacts.document(catalog['inventory_ref'])
    require(inventory['revision'] == catalog['revision'] and inventory['tree'] == catalog['tree'],
            'Inventory pin differs from migration definition')
    def git(*argv):
        return subprocess.check_output(['git', '--git-dir', str(args.source), *argv])
    require(git('rev-parse', catalog['revision'] + '^{tree}').decode().strip() == catalog['tree'],
            'Source tree differs from pin')
    actual = {}
    for line in git('ls-tree', '-r', '-l', '-z', catalog['revision']).split(b'\0'):
        if not line:
            continue
        head, path = line.split(b'\t', 1)
        mode, kind, oid, size = head.split()
        actual[base64.b64encode(path).decode()] = (mode.decode(), kind.decode(), oid.decode(),
                                                  int(size) if size != b'-' else None)
    expected = {e['path_base64']: (e['mode'], e['kind'], e['object_id'], e['size'])
                for e in inventory['entries']}
    require(actual == expected and len(actual) == catalog['tracked_paths'], 'Inventory does not cover Git tree')
    claims = {}
    doc_evidence = []
    documents = list((root / 'docs').glob('baldrix-*.md'))
    documents += list((root / 'docs/audits').glob('*baldrix*.md'))
    documents += [root / 'docs/native-routing-replay.md', root / 'docs/tool-hook-recovery-plan.md']
    for document in sorted(set(documents)):
        if not document.exists():
            continue
        body = document.read_text('utf-8')
        doc_ref = artifacts.put(body, 'migration-claim-document')['ref']
        handles = sorted(set(re.findall(r'sha256:[0-9a-f]{64}', body)))
        available, unavailable = [], []
        for handle in handles:
            try:
                artifacts.read(handle)
                available.append(handle)
            except (OSError, ValueError):
                unavailable.append(handle)
        note = {'document': document.relative_to(root).as_posix(), 'document_ref': doc_ref,
                'origin': 'Retained working-tree text; not a Git-reviewed path attestation',
                'retained_evidence_refs': available, 'unavailable_evidence_handles': unavailable}
        doc_evidence.append(note)
        for entry in inventory['entries']:
            path = base64.b64decode(entry['path_base64']).decode('utf-8', errors='backslashreplace')
            aliases = {path, path.removeprefix('scripts/')}
            if any(re.search(r'(?<![\w./-])' + re.escape(alias) + r'(?![\w./-])', body) for alias in aliases):
                claims.setdefault(path, []).append(note)
    service = build()
    with service.store.transaction() as tx:
        audit_ids = {row['id'] for row in tx.scan('research_audits')
                     if row['source']['commit'] == catalog['revision']}
        records = [r for r in tx.scan('research_paths') if r['audit_id'] in audit_ids]
        active = tx.get('deployment', 'active')
    automatic = {}
    for record in records:
        automatic.setdefault(record['record']['path'], []).append({
            'audit_id': record['audit_id'], 'path_base64': record['record']['path'],
            'disposition': record['record']['disposition']})
    reviews = json.loads(args.reviews.read_text('utf-8')) if args.reviews else []
    for review in reviews:
        body = git('cat-file', 'blob', review['object_id'])
        require(hashlib.sha256(body).hexdigest() == review['source_ref'][7:], 'Source evidence hash differs')
        require(artifacts.text(review['source_ref'], 1024 * 1024).encode('utf-8') == body, 'Source evidence differs')
        artifacts.read(review['analysis_ref'])
    report = reconcile(inventory, claims, automatic, reviews)
    report.update(observed_at=utcnow(), inventory_ref=catalog['inventory_ref'], documents=doc_evidence,
                  active=active, whole_migration_complete=False)
    receipt = artifacts.put(json.dumps(report, ensure_ascii=False), 'baldrix-path-ledger')
    output = root / '.runtime/baldrix-path-ledger.json'
    output.write_text(json.dumps({'artifact': receipt, **report}, ensure_ascii=False, indent=2), 'utf-8')
    csv_path = output.with_suffix('.csv')
    fields = ['path', 'object_id', 'size', 'source_read', 'semantic_review', 'adoption',
              'implementation_mapping', 'deployment_mapping', 'documents', 'automatic_dispositions']
    with csv_path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in report['rows']:
            writer.writerow({**{k: row[k] for k in fields if k in row},
                'documents': ';'.join(n['document'] for n in row['existing_claims']),
                'automatic_dispositions': ';'.join(n['disposition'] for n in row['automatic_records'])})
    with service.store.transaction() as tx:
        record = {'id': catalog['revision'], 'ledger_ref': receipt['ref'],
                  'at': report['observed_at'], 'summary': report['summary'], 'whole_migration_complete': False}
        tx.put('migration_ledger_snapshots', receipt['ref'], record)
        tx.put('migration_ledgers', catalog['revision'], record)
    print(json.dumps({'artifact': receipt, 'summary': report['summary'], 'csv': str(csv_path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
