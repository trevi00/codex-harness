"""Bounded compatibility preflight, not a complete Structured Outputs validator."""
import hashlib
import json

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from codex_harness.domain.model import ContractError, require

CAUSE = "codex-output-schema-version-missing-type"
SCOPE = "codex-harness/research-audit/output-schema"


def preflight(schema):
    try:
        encoded = json.dumps(schema, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError("Malformed outputSchema at $: expected JSON") from exc
    schema_hash = "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
    require(isinstance(schema, dict), f"outputSchema at $ must be an object; {schema_hash}")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        path = "$" + "".join(f"[{json.dumps(p)}]" for p in exc.path)
        raise ContractError(f"Malformed outputSchema at {path}: {exc.message}; {schema_hash}") from exc

    visited = set()

    def walk(node, path, version=False):
        if not isinstance(node, dict):
            return
        marker = (id(node), version)
        if marker in visited:
            return
        visited.add(marker)
        # INV-RECURRENCE-001: preserve the confirmed cause; never infer it from prompt text.
        if "const" in node and "type" not in node:
            cause = CAUSE if version else "codex-output-schema-constant-missing-type"
            raise ContractError(f"{cause}: {SCOPE} at {path}: const requires explicit type; {schema_hash}")
        ref = node.get("$ref", "")
        if version and ref.startswith("#/"):
            target = schema
            try:
                for part in ref[2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
            except (KeyError, TypeError):
                raise ContractError(f"Unresolved outputSchema reference at {path}: {ref}") from None
            walk(target, path + f"->$ref({ref})", True)
        for key in sorted(node):
            value = node[key]
            child_path = path + f"[{json.dumps(key)}]"
            if key in {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas"}:
                for name in sorted(value):
                    walk(value[name], child_path + f"[{json.dumps(name)}]",
                         key == "properties" and name == "version")
            elif key in {"anyOf", "allOf", "oneOf", "prefixItems"}:
                for index, child in enumerate(value):
                    walk(child, child_path + f"[{index}]", version)
            elif key in {"items", "contains", "additionalProperties", "unevaluatedProperties",
                         "unevaluatedItems", "propertyNames", "not", "if", "then", "else"}:
                walk(value, child_path, version)

    walk(schema, "$")
