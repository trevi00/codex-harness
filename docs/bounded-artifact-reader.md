# Bounded artifact reader

The standalone reader inspects one immutable artifact without constructing the harness,
PostgreSQL, Redis, embeddings, or a Codex runtime:

```text
python -m codex_harness.adapters.artifact_reader --root <artifact-root> --ref sha256:<digest> index --limit 8000
python -m codex_harness.adapters.artifact_reader --root <artifact-root> --ref sha256:<digest> pointer --pointer /receipt/answer --limit 8000
python -m codex_harness.adapters.artifact_reader --root <artifact-root> --ref sha256:<digest> pointer --pointer /receipt/answer --cursor <next_cursor> --limit 8000
python -m codex_harness.adapters.artifact_reader --root <artifact-root> --ref sha256:<digest> search --query blocked --limit 8000
```

Run these as argument vectors, without interpolating roots, references, pointers, or queries
into shell command text. Start with `index`, select the smallest useful RFC 6901 pointer,
and follow `next_cursor` until `truncated` is false. `page` exposes the original text when a
JSON projection is inappropriate. Search returns windows centered on matches, including for a
single-line artifact.

Pointer `content` is canonical JSON. Concatenating its pages reconstructs the selected value's
serialization; decode that completed string as JSON to recover the value. Page `content` is
original artifact text. Page, pointer, and search cursors count Unicode characters. An index
cursor is the ordinal of the next structural entry.

Per `INV-ARTIFACT-001`, `--limit` defaults to 8000 and accepts 512 through 32000 characters.
It includes the entire minified successful JSON written to stdout; stdout has no trailing newline,
and JSON escaping counts toward the limit. After argparse accepts a valid invocation, normal
reader and query errors are fixed, bounded JSON on stderr. Argparse usage errors and broken output
pipes retain their platform behavior. The reader only opens `<root>/<digest>.txt`, verifies its
SHA-256 and UTF-8, and never creates or searches a store. Full evidence remains unchanged in the
immutable artifact file.

This reader is one guardrail for reproducing a reference agent's bounded evidence lookup.
Static task-to-model routing alone does not establish equivalent behavior, and a CLI smoke test
does not qualify a lower-capability model for other tasks. Any transfer requires separately
recorded reference behavior, the same acceptance contract and hidden fixtures, and validated
execution for each harnessed model. This command and document do not record such certification.
