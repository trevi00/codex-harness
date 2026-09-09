"""Shared runtime record reference semantics for publication and collection."""

import re

from codex_harness.domain.model import canonical


def record_references(bucket: str, key: str, body: dict) -> set[str]:
    # INV-RESOURCE-001: fences are metadata, never collection roots. All other
    # record fields (including dictionary keys) participate in retention.
    if bucket == "artifact_tombstones":
        return set()
    return set(re.findall(r"sha256:[0-9a-f]{64}",
                          canonical({"bucket": bucket, "id": key, "body": body})))
