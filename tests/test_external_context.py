import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.research import ResearchSources
from codex_harness.application.rlm import RecursiveContext
from codex_harness.domain.model import ContractError


def test_artifact_bounds_search_and_tampering(tmp_path):
    artifacts = FileArtifacts(str(tmp_path))
    receipt = artifacts.put("first\nneedle\nlast", "fixture")
    assert artifacts.search(receipt["ref"], "needle") == [{"line": 2, "text": "needle"}]
    assert artifacts.read(receipt["ref"], 6, 6) == "needle"
    with pytest.raises(ContractError):
        artifacts.read("../../auth.json")
    (tmp_path / (receipt["ref"][7:] + ".txt")).write_text("changed")
    with pytest.raises(ContractError, match="modified"):
        artifacts.read(receipt["ref"])


def test_rlm_reads_external_ranges_and_stops_before_overspending(tmp_path):
    class Runtime:
        def run(self, *args):
            return {"answer": {"finding": "fixture finding", "sufficient": True}}

    artifacts = FileArtifacts(str(tmp_path))
    ref = artifacts.put("x" * 9000, "fixture")["ref"]
    rlm = RecursiveContext(artifacts, Runtime(), str(tmp_path), max_calls=4, chunk_size=3000)
    result = rlm.analyze(ref, "Find the relevant facts")
    assert rlm.calls == 4 and result["range"] == [0, 9000]
    too_small = RecursiveContext(artifacts, Runtime(), str(tmp_path), max_calls=3, chunk_size=3000)
    with pytest.raises(ContractError, match="budget"):
        too_small.analyze(ref, "Find facts")
    assert too_small.calls == 0


def test_research_parsers_capture_primary_links():
    html = '<article><h2><a href="/owner/repo">owner/repo</a></h2><p>Useful &amp; small</p></article>'
    assert ResearchSources.parse_github(html)[0] == {
        "url": "https://github.com/owner/repo", "title": "owner/repo", "summary": "Useful & small"}
    xml = '<rss><channel><item><title>News</title><link>https://example.org/item</link><description>Evidence</description></item></channel></rss>'
    assert ResearchSources.parse_feed(xml)[0]["url"] == "https://example.org/item"
