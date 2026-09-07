# Reference audit coverage

Captured 2026-09-07 from locally fetched origin HEADs. These are complete tracked-file
inventories, **not completed semantic audits or executed upstream tests**. PostgreSQL
`reference_audits` retains each immutable manifest and its transitive text artifacts.
Binary/non-UTF-8 entries retain object IDs and hashes, and require separate inspection.

| Repository | Pinned commit | Paths | UTF-8 artifacts | Coverage status |
|---|---|---:|---:|---|
| trevi00/harness | `93d56e4f4553c682c1008b63dba3830f4e2f046d` | 556 | 556 | Inventoried; semantic coverage pending |
| trevi00/harness-guardian | `8d13d3b4b26dcac9eca2a9e414966a1247ebf39d` | 11 | 11 | Inventoried; semantic coverage pending |
| trevi00/baldrix | `b9586c59c062457a45018e41c2e753934b5ca6c9` | 1648 | 1648 | Inventoried; semantic coverage pending |
| witt3rd/oh-my-hermes | `2a98d38b43010a438b316fb48dbe68a3c8ee8fed` | 120 | 120 | Inventoried; semantic coverage pending |
| Q00/ouroboros | `1fc754e7b7599b3df057660bcc6af37241183766` | 1806 | 1795 | Inventoried; semantic coverage pending |

## Manifest references

- trevi00/harness: `sha256:18cf0c27d54f21227142177466ddd49fb985707d648fc4a59f0d76370ab68575`
- trevi00/harness-guardian: `sha256:d0ccfc9b562bae61cb9f808dc73437d42a949df0e7b95f407075098e6c6551fa`
- trevi00/baldrix: `sha256:98671feace0a361dda330248686c0c6b7fd3a07c43d0fc426a2ff9f552ad605b`
- witt3rd/oh-my-hermes: `sha256:9f6fd3682aa653a07622b39805a233acf60730596db2f6a81f48dd96874d7141`
- Q00/ouroboros: `sha256:f0d0cca5ed0bd22bc50a269e665f77fdf0d94f98330efecb196a03648d4acc4d`

The earlier notes in references.md remain limited-scope observations. No upstream
repository is designated fully analyzed or safe to copy on the basis of this inventory.
Reviewers must use research-standard.md and retain source-to-implementation evidence.

## Audit lifecycle implementation

The five pins above remain packaged in `resources/research-backlog.json`. The seed use case validates
historical manifests and preserves original PostgreSQL records. The scheduler now acquires pinned Git
objects and queues bounded semantic audit partitions; imports themselves do not mark coverage.
No live seed or semantic review of these five repositories was performed in this task.

The acquisition, runner receipt, independent review, scheduling and release/rollback paths are described
in `research-standard.md`. This candidate's local checks and verification limitations are recorded in
`audit-lifecycle-review-evidence.md`. Fixture reviews/canaries must not be interpreted as production
verification. All upstream coverage statuses in the table remain unchanged.
