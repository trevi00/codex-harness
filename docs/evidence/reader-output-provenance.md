# Bounded reader provenance and source-review admission

The completed read-only production inventory on 87b1b3 visited 52,991 identifiers.
It reported 66 missing identities. Four exact original review receipts have now
been restored; these restorations do not rewrite historical outcomes or certify
transitive graph closure. The archived inventory remains unchanged.

One runtime-event parent, 71b2d5dd56570d115861d8ae3595aec121dcbcdb307ba809b8c52f35ef2daa39,
contains a truncated artifact-query pointer result. Its 21 apparent missing nodes
are upstream package-download hashes. The original content-addressed artifact is
fddc708148d56fdb1249add00b7a200b488ef2392c96ba89ebebfba654ba2979. The original bytes
reproduce all 8,000 output characters exactly using the existing pointer reader.
The Git-owned binding pins the parent, command, output and original digest. Only
that exact output occurrence is projected to its original reference. Other fields
remain intact; the original is traversed in full. Independently existing blobs
continue to be retained by the collector. No global digest exemption is introduced.
The actual parent now has two available dependencies, and the complete original
has no local artifact dependencies. This is a bounded result, not GC clearance.

Independent native task 474b9a9f-1d19-44be-b858-df2b8579f86e rejected the prior
4dc83ed source: ordinary source review could approve without successful command
inspection. Its negative control and execution remain preserved. The executor now
requires successful command inspection for every accepted source review before
creating an approval or downstream outbox, in addition to shared evidence admission.
Regression cases independently cover unpublished evidence and published evidence
without inspection; ordinary retry can succeed only after both requirements hold.

Collection and automatic deployment remain paused. Final exact-candidate source
review, explicit evaluator migration approval, full isolated host qualification
and actual CLI canaries remain required. No full upstream migration is claimed.
