# Python runner reference repair

Task: `788d4d61-0135-4aea-96fe-a803ab95a3bf`.
Base: `e68d5e157465b4b03193ee3feeb3a776473b8d40`.
Previous candidate: `19c4d73c879bef32909307186e8196a682cdbcbd`, restored in full
by local commit `6fa275e` before this repair. Its historical evidence remains
unchanged, including failures. Duplicate-JSON and unknown inspection-option
retention, compact measurement replay, fixture cleanup and DB lock changes remain.

Inputs inspected through the bounded artifact reader:
- Assignment: `sha256:aad564ac7987bab87d68a602fec5961cbb510d608aa960ab09f1b15712093495`.
- Finding: `sha256:5de17c578341c70e3d12cfdf521986ec66be2541a42e7eabe9c46ae87a9931d3`.
- Optional patch: `sha256:bacddaffe1a2db3a36230cc7e93f838a7c5d7a931a7f022e06e1538a6d5fb942`
  (text, so JSON index failed; raw page read succeeded).
- Original runner: `sha256:b967dca2a7a4cf978c06c0f08198ac4677b4fa28fa3e3d20a0da2d8abbf85855`.
  Its sidecar identifies source `baldrix-budget-probe-runner` and 3010 bytes.
  The fixture preserves those exact bytes; it is parsed, never executed.

The runner contains a literal image operand following two f-string mount values.
The previous decoder reports that operand as an artifact dependency;
`negative-control.json` records this reproduction against the previous decoder's
Git bytes. This is a local negative control, not independent recurrence or review.

The optional patch informed the AST approach. This repair additionally bypasses
generic diagnostic parsing for runner text, preserves comments and other source
literals, rejects starred expansion, and retains concatenated literals rather than
removing evidence comments within an AST span. AST offsets are UTF-8 byte offsets.
Only the exact source kind selects this policy; the maintenance caller validates
artifact content hash and sidecar identity/length before traversing dependencies.

New regression coverage includes original bytes, malformed/truncated Python,
unknown flags, dynamic image operands, dynamic option values, starred expansion,
Unicode before an operand on the same line, CRLF, comments, source scoping,
same-identity evidence elsewhere, and traversal with corrupt metadata.

Qualification remains incomplete. No independent lead/conductor review, fresh
incumbent service integration suite, production graph dry run, host/container
writer convergence review, or actual exact-candidate CLI canary was performed.
Worker tests are not release qualification. Service tests skipped by pytest remain
unverified. No production runtime state was read or changed; collection must stay
paused until current production traversal and reviewed writer convergence, followed
by all INV-RELEASE-001 gates. No migration-complete claim is made. Nothing was
pushed, merged or deployed.

Initial validation is retained: Ruff found an import-order error (corrected), and
the full suite reported 1 failed, 693 passed, 34 skipped. The new corrupt-metadata
test incorrectly expected a deferred-result dictionary; the existing collector
raises ContractError. Its assertion was corrected to require that fail-closed
exception. Production behavior was not changed to accommodate the test.
The initial focused reference suite passed all 98 tests.

Preservation check: 18 of the previous candidate's 22 changed paths are byte-for-byte
identical to commit `19c4d73`; four paths contain additive runner changes. A later
check also covered standalone CR newlines and conservative handling when an AST
string span cannot tokenize in isolation. Intermediate passing suite logs are
retained; only the final `pytest.log` corresponds to all final code changes.
Final command results and SHA-256 bindings are recorded in `validation.json`.
