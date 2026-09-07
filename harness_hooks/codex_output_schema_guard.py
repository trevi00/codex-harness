"""SessionStart reminder only: native hook input does not expose outputSchema."""
import json
import sys

REMINDER = (
    "INV-RECURRENCE-001: research output schemas must retain integer type and const=1 "
    "on version fields, including nested definitions. The harness adapter preflight "
    "rejects untyped constants before CLI or app-server submission. Preserve the schema "
    "hash, offending path, revision and provider error when diagnosing a failure. "
    "Confirm cause from schema bytes; other invalid_json_schema errors are separate "
    "diagnoses, and retry/redelivery alone is not independent recurrence. "
    "This SessionStart hook cannot "
    "inspect or repair outputSchema. Schema errors are failed executions, not accepted "
    "audits or reviews. INV-RELEASE-001 requires independent reviews and actual canaries."
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
