from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path

import psycopg
import tree_sitter_python
from psycopg.types.json import Jsonb
from tree_sitter import Language, Parser

from codex_harness.domain.model import ContractError, require

SKIP = {".git", ".venv", "node_modules", "__pycache__", ".runtime", ".pytest_cache", ".ruff_cache"}


def extract_python(root: str) -> dict:
    base = Path(root).resolve()
    require(base.is_dir(), "Repository not found")
    parser = Parser(Language(tree_sitter_python.language()))
    nodes, edges = [], []
    fingerprints = []
    for directory, children, names in os.walk(base):
        children[:] = sorted(n for n in children if n not in SKIP and not Path(directory, n).is_symlink())
        for name in sorted(names):
            path = Path(directory, name)
            if path.suffix != ".py" or path.is_symlink():
                continue
            raw = path.read_bytes()
            tree = parser.parse(raw)
            if tree.root_node.has_error:
                raise ContractError(f"Parse failed: {path.relative_to(base)}")
            relative = path.relative_to(base).as_posix()
            revision = hashlib.sha256(raw).hexdigest()
            fingerprints.append((relative, revision))
            file_id = f"file:{base.name}:{relative}"
            nodes.append({"id": file_id, "repository": str(base), "kind": "file",
                          "body": relative, "source_ref": relative, "revision": revision,
                          "properties": {"language": "python"}})

            def visit(node, parent_id, qualified):
                current_parent, current_qualified = parent_id, qualified
                if node.type in {"function_definition", "class_definition"}:
                    symbol = node.child_by_field_name("name").text.decode()
                    current_qualified = qualified + [symbol]
                    node_id = f"symbol:{base.name}:{relative}:{'.'.join(current_qualified)}:{node.start_point.row + 1}"
                    nodes.append({"id": node_id, "repository": str(base), "kind": node.type,
                                  "body": node.text.decode()[:6000],
                                  "source_ref": f"{relative}:{node.start_point.row + 1}",
                                  "revision": revision, "properties": {"name": symbol}})
                    edges.append((parent_id, node_id, "contains"))
                    current_parent = node_id
                elif node.type == "comment":
                    for rule_id in re.findall(rb"@invariant\s+([A-Z0-9-]+)", node.text):
                        rule = rule_id.decode()
                        rule_node = f"rule:{base.name}:{rule}"
                        if not any(n["id"] == rule_node for n in nodes):
                            nodes.append({"id": rule_node, "repository": str(base), "kind": "rule_reference",
                                          "body": rule, "source_ref": f"{relative}:{node.start_point.row + 1}",
                                          "revision": revision, "properties": {"trust": "declared"}})
                        edges.append((parent_id, rule_node, "references"))
                for child in node.named_children:
                    visit(child, current_parent, current_qualified)

            visit(tree.root_node, file_id, [])
    snapshot = hashlib.sha256(repr(fingerprints).encode()).hexdigest()
    return {"repository": str(base), "snapshot": snapshot, "nodes": nodes, "edges": edges}


class PostgresKnowledge:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def index_python(self, root: str) -> dict:
        graph = extract_python(root)
        with psycopg.connect(self.dsn) as conn:
            conn.execute("SELECT pg_advisory_xact_lock(734220)")
            # Full replace only after all parses succeed; old index survives failures.
            conn.execute("DELETE FROM knowledge_nodes WHERE repository=%s", (graph["repository"],))
            for n in graph["nodes"]:
                conn.execute("""INSERT INTO knowledge_nodes
                    (id,repository,kind,body,source_ref,revision,properties)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                             (n["id"], n["repository"], n["kind"], n["body"], n["source_ref"],
                              n["revision"], Jsonb({**n["properties"], "snapshot": graph["snapshot"]})))
            for source, target, kind in graph["edges"]:
                conn.execute("INSERT INTO knowledge_edges VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                             (source, target, kind))
        return {"snapshot": graph["snapshot"], "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}

    def query(self, text: str, depth: int = 1, limit: int = 12) -> list[dict]:
        require(bool(text.strip()) and 0 <= depth <= 3 and 1 <= limit <= 100, "Invalid graph query")
        with psycopg.connect(self.dsn) as conn:
            seeds = [r[0] for r in conn.execute("""SELECT id FROM knowledge_nodes
                WHERE body ILIKE %s ORDER BY id LIMIT %s""", (f"%{text}%", limit))]
            found = set(seeds)
            for _ in range(depth):
                rows = conn.execute("""SELECT source,target FROM knowledge_edges
                    WHERE source=ANY(%s) OR target=ANY(%s) ORDER BY source,target LIMIT 500""",
                                    (sorted(found), sorted(found))).fetchall()
                found.update(value for row in rows for value in row)
            rows = conn.execute("""SELECT id,kind,body,source_ref,revision,properties
                FROM knowledge_nodes WHERE id=ANY(%s)
                ORDER BY CASE WHEN id=ANY(%s) THEN 0 ELSE 1 END,id LIMIT %s""",
                                (sorted(found), seeds, limit)).fetchall()
        return [dict(zip(("id", "kind", "body", "source_ref", "revision", "properties"), r)) for r in rows]

    @staticmethod
    def vector(values: list[float]) -> str:
        require(bool(values) and all(math.isfinite(v) for v in values), "Invalid embedding")
        return "[" + ",".join(str(float(v)) for v in values) + "]"

    def set_embedding(self, node_id: str, values: list[float], model: str) -> None:
        require(bool(model), "Embedding model ID required")
        with psycopg.connect(self.dsn) as conn:
            result = conn.execute("""UPDATE knowledge_nodes SET embedding=%s::vector,
                properties=properties || %s WHERE id=%s""",
                                  (self.vector(values), Jsonb({"embedding_model": model}), node_id))
            require(result.rowcount == 1, "Knowledge node not found")

    def vector_query(self, values: list[float], model: str, limit: int = 12) -> list[dict]:
        require(1 <= limit <= 100, "Invalid limit")
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute("""SELECT id,source_ref,revision,embedding <=> %s::vector AS distance
                FROM knowledge_nodes WHERE embedding IS NOT NULL
                AND vector_dims(embedding)=%s AND properties->>'embedding_model'=%s
                ORDER BY distance,id LIMIT %s""", (self.vector(values), len(values), model, limit))
            return [dict(zip(("id", "source_ref", "revision", "distance"), r)) for r in rows]
