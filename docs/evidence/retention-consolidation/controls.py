"""Reproduce rejected decoders in memory without touching production artifacts."""
import hashlib
import json
import subprocess
from pathlib import Path

from codex_harness.adapters.record_references import artifact_references

out = []
ref = 'sha256:' + 'a' * 64
for rev, body, kwargs in [
    ('34da547aa6d8fc162ac9890cc5cd40d6a3d138b3',
     {'stdout': '{"candidate":{},"image":"' + ref + '","image":"unknown","truncated":'}, {}),
    ('5dc00f184a6bfff450d4fd090aa1bff13e1e036f',
     {'stdout': '{"candidate":{},"image":"' + ref + '","image":"unknown"}'}, {}),
    ('5dc00f184a6bfff450d4fd090aa1bff13e1e036f',
     {'argv': ['docker', 'image', 'inspect', '--unknown', 'target', '--format', '{{.Id}}'],
      'stdout': ref}, {}),
    ('19c4d73c879bef32909307186e8196a682cdbcbd',
     Path('tests/fixtures/reference_runner/original.txt').read_text(),
     {'source': 'baldrix-budget-probe-runner'}),
]:
    argv = ['git', 'show', rev + ':src/codex_harness/adapters/record_references.py']
    source = subprocess.check_output(argv)
    namespace = {}
    exec(compile(source, rev + '/record_references.py', 'exec'), namespace)
    old = sorted(namespace['artifact_references'](body, **kwargs))
    new = sorted(artifact_references(body, **kwargs))
    assert old != new
    out.append({'argv': argv, 'revision': rev,
                'source_sha256': hashlib.sha256(source).hexdigest(), 'input': body,
                'kwargs': kwargs, 'rejected_dependencies': old, 'candidate_dependencies': new,
                'scope': 'Decoder-only negative control; not a review or independent recurrence'})
print(json.dumps(out, indent=2))
