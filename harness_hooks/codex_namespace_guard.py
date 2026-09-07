"""Native SessionStart reminder; structured AppServer replay for incident fixtures.

Codex 0.153.4 startup errors bypass PostToolUse, whose Bash response also lacks
exit status. The adapter enforces containment; this native hook does not claim
to observe future failures or repair the host. No files or settings are changed.
"""

import json
import sys

DENIAL = "bwrap: No permissions to create a new namespace"
REMINDER = (
    "Independent reviews require successful command inspection. If required inspection "
    "fails with bubblewrap namespace creation denied, report inspection-blocked and do "
    "not accept the review. Preserve command evidence. Do not change sandbox permissions, "
    "host sysctls, or container privileges. Detection does not confirm or fix the host cause."
)
BLOCK = {"decision": "block", "reason": "inspection-blocked: " + DENIAL}


def evaluate(value):
    if not isinstance(value, dict):
        return None
    if value.get("hook_event_name") == "SessionStart":
        if (value.get("source") in ("startup", "resume", "clear", "compact")
                and all(isinstance(value.get(k), str) and value[k]
                        for k in ("session_id", "cwd"))):
            return {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                           "additionalContext": REMINDER}}
        return None
    # Offline replay only: these are AppServer events, NOT native lifecycle stdin.
    # INV-RELEASE-001: authoritative containment lives in the AppServer adapter.
    if value.get("method") != "item/completed":
        return None
    params = value.get("params")
    if (not isinstance(params, dict)
            or not all(isinstance(params.get(k), str) and params[k]
                       for k in ("threadId", "turnId"))):
        return None
    item = params.get("item")
    if (isinstance(item, dict) and item.get("type") == "commandExecution"
            and isinstance(item.get("id"), str) and bool(item["id"])
            and item.get("status") == "failed"
            and type(item.get("exitCode")) is int and item["exitCode"] != 0
            and isinstance(item.get("aggregatedOutput"), str)
            and DENIAL in item["aggregatedOutput"]):
        return BLOCK
    return None


def main():
    try:
        output = evaluate(json.load(sys.stdin))
    except (ValueError, UnicodeError, RecursionError):
        output = None
    if output is not None:
        print(json.dumps(output))


if __name__ == "__main__":
    main()
