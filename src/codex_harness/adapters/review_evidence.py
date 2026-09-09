"""Admission check for shared evidence cited by an accepted source review."""
from codex_harness.adapters.record_references import artifact_references
from codex_harness.domain.model import ContractError


def validate_review_evidence(artifacts, result):
    if result.get('accepted') is not True:
        return
    # INV-RELEASE-001 / INV-RESOURCE-001: a scratch-file digest is not a
    # published evidence handle. FileArtifacts.read verifies the complete bytes.
    for reference in sorted(artifact_references(result)):
        try:
            artifacts.read(reference, length=1)
        except (OSError, ValueError) as exc:
            # Keep the identity as a digest observation, not another dangling ref.
            raise ContractError('Review cites unavailable or corrupt shared evidence; hex='
                                + reference[7:]) from exc
