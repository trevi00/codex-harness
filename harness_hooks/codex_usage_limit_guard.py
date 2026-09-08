"""SessionStart diagnostic reminder only; no provider observation or quota control."""
import json
import sys

REMINDER = (
    "INV-RECURRENCE-001: usageLimitExceeded is a Codex provider usage-limit failure. "
    "Preserve the exact provider error, task ID, attempt, revision and immutable evidence references. "
    "Report quota-blocked executions as failures, never successful audits, reviews or canaries. "
    "Distinguish usageLimitExceeded from schema, authentication and transient errors; "
    "confirm cause and scope from evidence. Retries and redelivery alone are not independent recurrence. "
    "Affected account, quota category and underlying accounting may be unknown; "
    "do not infer a reset timezone. This SessionStart hook cannot observe future provider errors, "
    "restore quota, or suppress executor retries. The adapter/application marks the affected execution failed and nonretryable; recovery requires a fresh authorized assignment after external quota recovery. INV-RELEASE-001 requires independent reviews "
    "and actual successful canaries."
)


def main():
    try:
        value = json.load(sys.stdin)
    except (ValueError, UnicodeError):
        return
    if (isinstance(value, dict) and value.get("hook_event_name") == "SessionStart"
            and value.get("source") in ("startup", "resume", "clear", "compact")
            and all(isinstance(value.get(k), str) and value[k] for k in ("session_id", "cwd"))):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": REMINDER}}))


if __name__ == "__main__":
    main()
