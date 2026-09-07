from pathlib import Path

import pytest

from codex_harness.adapters.commands import run_process
from codex_harness.adapters.git import GitWorkspace
from codex_harness.domain.model import ContractError


def git(root, *args):
    result = run_process(["git", *args], cwd=str(root))
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def repository(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@localhost")
    (root / "original.txt").write_text("original", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "Initial fixture")
    return root


def test_candidate_isolation_commit_capture_and_exact_merge(tmp_path):
    root = repository(tmp_path)
    adapter = GitWorkspace(str(root), str(tmp_path / "workspaces"))
    workspace = adapter.prepare("task-one", "HEAD")
    (Path(workspace["path"]) / "change.txt").write_text("review me", encoding="utf-8")
    candidate = adapter.capture(workspace)
    assert not (root / "change.txt").exists()
    assert adapter.inspect(candidate["revision"], candidate["base"])["files"] == ["change.txt"]
    review = adapter.review_workspace(candidate["revision"], "review-one")
    assert (Path(review) / "change.txt").read_text() == "review me"
    assert adapter.merge(candidate)["merged"]
    assert (root / "change.txt").read_text() == "review me"


def test_main_advance_invalidates_previous_merge_approval(tmp_path):
    root = repository(tmp_path)
    adapter = GitWorkspace(str(root), str(tmp_path / "workspaces"))
    workspace = adapter.prepare("task-one", "HEAD")
    (Path(workspace["path"]) / "change.txt").write_text("candidate")
    candidate = adapter.capture(workspace)
    (root / "other.txt").write_text("new main")
    git(root, "add", ".")
    git(root, "commit", "-m", "Concurrent change")
    with pytest.raises(ContractError, match="Main changed"):
        adapter.merge(candidate)
