import json
from types import SimpleNamespace

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.executor import VERDICT, Executor
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.service import Harness
from codex_harness.bootstrap import organization


def test_review_boundary_survives_large_diff_and_context_rotation(tmp_path, monkeypatch):
    prompts = []

    class Runtime:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def run(self, prompt, *args, **kwargs):
            prompts.append(json.loads(prompt))
            return {'answer': {'accepted': False, 'blocked': True, 'reason': 'source inspection unavailable'},
                    'thread_id': str(len(prompts)), 'usage': {}, 'events': [],
                    'rotate': len(prompts) == 1, 'interrupted': len(prompts) == 1}

    monkeypatch.setattr('codex_harness.adapters.executor.AppServer', Runtime)
    service = Harness(MemoryStore(), organization())
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    executor = Executor(service, SimpleNamespace(_git=lambda *a, **k: 'revision'), artifacts)
    evidence = {'candidate': {'revision': 'revision', 'base': 'base', 'tree': 'tree'},
                'independent_diff': 'large source diff\n' * 20000}
    result = executor._run('lead:improvement', 'review', 'Review candidate', evidence,
                           str(tmp_path), VERDICT, read_only=True)
    assert len(prompts) == 2
    for prompt in prompts:
        assert len(json.dumps(prompt, ensure_ascii=False).encode()) < 22000
        contract = prompt['required']['review_contract']
        assert contract['qualification_owner'] == 'Host ReleaseRunner'
        assert 'does not verify or promote' in contract['approval_effect']
        assert 'actual Codex startup and file-task canaries' in contract['promotion_requires']
        assert prompt['required']['task_contract']['candidate'] == evidence['candidate']
        assert json.loads(artifacts.text(prompt['required']['external_context']['ref'], 1000000)) == evidence
    assert result['blocked'] and not result['accepted']
    with service.store.transaction() as tx:
        assert not tx.scan('releases') and not tx.scan('release_queue')
