"""Characterize pinned upstream defects; passing probes do NOT mean defects are fixed.

Execute only in the documented isolated container with upstream scripts on PYTHONPATH.
No upstream source is modified. Fault injection is explicit and confined to each test.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from lib import budget, event_store, event_taxonomy, paths


class BudgetCharacterization(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_normal_accumulation_and_successful_once_delivery(self):
        budget.record_invocation('normal', 'abc', base_dir=self.base)
        budget.record_invocation('normal', 'de', base_dir=self.base)
        delivered = []
        self.assertEqual(budget.get_total_chars('normal', base_dir=self.base), 5)
        self.assertTrue(budget.check_and_emit_exceeded(
            'normal', cap=5, base_dir=self.base, emit_fn=lambda *args: delivered.append(args)))
        self.assertFalse(budget.check_and_emit_exceeded(
            'normal', cap=5, base_dir=self.base, emit_fn=lambda *args: delivered.append(args)))
        self.assertEqual(len(delivered), 1)

    def test_failed_delivery_claims_success_and_suppresses_retry(self):
        budget.record_invocation('delivery', 'abc', base_dir=self.base)
        attempts = []

        def fail(*args):
            attempts.append(args)
            raise OSError('injected delivery failure')

        self.assertTrue(budget.check_and_emit_exceeded(
            'delivery', cap=1, base_dir=self.base, emit_fn=fail))
        self.assertFalse(budget.check_and_emit_exceeded(
            'delivery', cap=1, base_dir=self.base, emit_fn=fail))
        self.assertEqual(len(attempts), 1)

    def test_distinct_session_ids_share_accounting(self):
        budget.record_invocation('a/b', 'abc', base_dir=self.base)
        budget.record_invocation('ab', 'de', base_dir=self.base)
        self.assertEqual(budget.get_total_chars('a/b', base_dir=self.base), 5)
        self.assertEqual(budget.get_invocation_count('ab', base_dir=self.base), 2)

    def test_failed_write_returns_unpersisted_success_record(self):
        with patch.object(budget, 'write_json_atomic', return_value=False):
            returned = budget.record_invocation('lost', 'abc', base_dir=self.base)
        self.assertEqual(returned['total_chars'], 3)
        self.assertEqual(budget.get_total_chars('lost', base_dir=self.base), 0)

    def test_two_writers_reading_same_snapshot_lose_one_increment(self):
        budget.record_invocation('race', '', base_dir=self.base)
        real_read = budget.read_json
        barrier = Barrier(2)

        def synchronized_read(*args, **kwargs):
            snapshot = real_read(*args, **kwargs)
            barrier.wait(timeout=5)
            return snapshot

        with patch.object(budget, 'read_json', side_effect=synchronized_read):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(budget.record_invocation, 'race', text,
                                       base_dir=self.base) for text in ('abc', 'defg')]
                for future in futures:
                    future.result(timeout=10)
        self.assertIn(budget.get_total_chars('race', base_dir=self.base), (3, 4))
        self.assertEqual(budget.get_invocation_count('race', base_dir=self.base), 2)

    def test_budget_imported_root_does_not_follow_dynamic_state_override(self):
        changed = self.base / 'new-state'
        with patch.dict('os.environ', {'CLAUDE_STATE_DIR': str(changed)}):
            self.assertEqual(paths.state_dir(), changed)
            self.assertNotEqual(budget._budget_dir(), changed / 'budgets')

    def test_taxonomy_swallows_known_event_delivery_failure(self):
        attempts = []

        def fail(*args):
            attempts.append(args)
            raise OSError('injected event-store failure')

        self.assertIsNone(event_taxonomy.emit_with_validation('budget.exceeded', {}, fail))
        self.assertEqual(len(attempts), 1)

    def test_actual_hook_imports_missing_module_level_append(self):
        hook_path = paths.SCRIPTS_DIR / 'handlers/post_tool/agent_outcome_audit.py'
        spec = importlib.util.spec_from_file_location('upstream_outcome_hook', hook_path)
        hook = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hook)
        self.assertFalse(hasattr(event_store, 'append'))
        budget.record_invocation('hook', 'abc', base_dir=self.base)
        with patch.object(event_store.EventStore, 'append') as append:
            self.assertTrue(budget.check_and_emit_exceeded(
                'hook', cap=1, base_dir=self.base, emit_fn=hook._event_emit))
            append.assert_not_called()
        self.assertFalse(budget.check_and_emit_exceeded(
            'hook', cap=1, base_dir=self.base, emit_fn=hook._event_emit))

    def test_emission_overwrites_intervening_usage_increment(self):
        budget.record_invocation('interleaved', 'abc', base_dir=self.base)

        def concurrent_usage(*args):
            budget.record_invocation('interleaved', 'defgh', base_dir=self.base)

        self.assertTrue(budget.check_and_emit_exceeded(
            'interleaved', cap=1, base_dir=self.base, emit_fn=concurrent_usage))
        self.assertEqual(budget.get_total_chars('interleaved', base_dir=self.base), 3)
        self.assertEqual(budget.get_invocation_count('interleaved', base_dir=self.base), 1)

    def test_hook_main_records_budget_but_no_budget_event(self):
        state = self.base / 'state'
        env = {**os.environ, 'CLAUDE_STATE_DIR': str(state),
               'CLAUDE_HOME': str(self.base / 'home'),
               'CLAUDE_TELEMETRY_DIR': str(self.base / 'telemetry'), 'BUDGET_CHAR_CAP': '1'}
        result = subprocess.run(
            [sys.executable, str(paths.SCRIPTS_DIR / 'handlers/post_tool/agent_outcome_audit.py')],
            input=json.dumps({'tool_name': 'Agent', 'session_id': 'subprocess',
                              'tool_input': {'subagent_type': 'audit-fixture-nonexistent'},
                              'tool_response': 'abc'}),
            env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        recorded = json.loads((state / 'budgets/subprocess.json').read_text())
        self.assertEqual(recorded['total_chars'], 3)
        self.assertTrue(recorded['exceeded_emitted'])
        for log in state.rglob('*.jsonl'):
            self.assertNotIn('budget.exceeded', log.read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
