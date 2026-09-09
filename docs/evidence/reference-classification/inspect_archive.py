"""Read-only reclassification of every parent in the supplied partial archive."""
import hashlib
import json
from pathlib import Path

from codex_harness.adapters.maintenance import ArtifactMaintenance

HERE = Path(__file__).parent
ROOT = Path('/runtime/artifacts')
archive = json.loads((HERE / 'archived-inventory.json').read_text())
parents = {}
for ref, item in archive['missing'].items():
    for parent in item['parents']:
        parents.setdefault(parent, []).append(ref)
results = []
cache = {}
existing = ArtifactMaintenance._existing(ROOT)
for parent, references in sorted(parents.items()):
    path = ROOT / (parent[7:] + '.txt')
    row = {'parent': parent, 'archived_missing': references}
    try:
        content = path.read_bytes()
        assert hashlib.sha256(content).hexdigest() == parent[7:]
        metadata = json.loads(path.with_suffix('.json').read_text())
        row['source'] = metadata.get('source')
        deps = ArtifactMaintenance._dependencies(path, content, cache, existing)
        row['still_required'] = sorted(set(references) & deps)
        row['typed_exclusions'] = sorted(set(references) - deps)
        text = content.decode()
        row['occurrences'] = {ref: [text[max(0, m-180):m+len(ref)+180]
                                  for m in [text.find(ref)] if m >= 0]
                              for ref in references}
        row['status'] = 'inspected'
    except Exception as exc:
        row.update(status='failed', error=str(exc))
    results.append(row)
    (HERE / "parent-inspection.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"completed": len(results), "parent": parent, "status": row["status"]}), flush=True)
(HERE / 'parent-inspection.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({'parents': len(results), 'failed': sum(r['status'] == 'failed' for r in results),
                  'remaining_edges': sum(len(r.get('still_required', [])) for r in results)}))
