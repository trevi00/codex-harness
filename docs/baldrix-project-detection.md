# Project detection and initialization

Scope: Baldrix b9586c59 `skill_match.PROJECT_FILE_SIGNALS`, `PROJECT_DIR_SIGNALS`,
and `detect_project_type`, adapted to explicit-root initialization. All 17 filename
signals and the workflow-directory signal are retained. The old detector required a
pre-existing `.claude` marker and walked upward; initialization must work before that
marker exists, so this command takes an explicit root and does not scan parent, nested
or home directories. This is not recursive monorepo discovery.

```
python scripts/project_init.py PROJECT_ROOT --detect --preview
python scripts/project_init.py PROJECT_ROOT --detect
```

Preview performs no writes. Initialization uses the same exclusive-create path as
explicit YAML configuration/import. Commit the resulting `.harness/tech-stack.yaml`
for the existing Git-pinned Executor routing to consume it. It never overwrites an
existing project definition.

Detection reads bounded regular files without evaluating setup.py, Gradle, Gemfiles,
package scripts or installation commands. Signal metadata records exact content hashes.
The result is provisional: filename presence and declared dependencies do not establish
that a framework is installed or used at runtime. Unknown roots retain empty stacks and
an explicit unknown detection status. Docker/CI signals are metadata, not programming
languages. All other source categories become language candidates.

Node projects distinguish TypeScript by tsconfig.json or declared typescript; otherwise
the JavaScript toolchain is inferred. Known framework declarations produce framework
candidates. All observed dependency scopes/ranges for those frameworks are retained,
including conflicting declarations; no exact skill version is invented from a range.
Python requires-python is retained as a declaration, not an installed interpreter.
Malformed package/pyproject data, duplicate JSON keys, oversized or non-regular manifest
paths fail explicitly before any configuration write.

Tests cover every original signal category, non-execution of project scripts, framework
ranges/conflicts, source hashes, unknown/nested/home boundaries, malformed manifests,
size/file-type limits, and actual CLI preview/initialization/no-overwrite behavior.
Claude review and candidate canaries are retained separately. Full stage selection,
ranking, asset migration, recursive workspace modeling and runtime proof remain open.
