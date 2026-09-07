import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_inner_layers_do_not_import_adapters_or_sdk():
    banned = {"psycopg", "redis", "tree_sitter", "tree_sitter_python", "subprocess", "jsonschema"}
    for folder in ("domain", "application"):
        for source in (ROOT / "src/codex_harness" / folder).rglob("*.py"):
            tree = ast.parse(source.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                imports = ([node.module or ""] if isinstance(node, ast.ImportFrom)
                           else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
                for module in imports:
                    assert module.split(".")[0] not in banned, (source, module)
                    assert not module.startswith("codex_harness.adapters"), (source, module)
                    assert not module.startswith("codex_harness.bootstrap"), (source, module)


def test_invariant_comments_resolve_to_contract_registry():
    contracts = (ROOT / "docs/contracts.md").read_text(encoding="utf-8")
    for source in (ROOT / "src").rglob("*.py"):
        for identifier in re.findall(r"@invariant\s+(INV-[A-Z0-9-]+)", source.read_text(encoding="utf-8")):
            assert identifier in contracts, (source, identifier)
