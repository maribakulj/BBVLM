"""Regression tests for experiment evidence lost during bundle/resume."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    'loop_runner', Path(__file__).resolve().parents[1] / 'scripts/autonomous_loop.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CheckpointResumeTest(unittest.TestCase):
    def test_external_evidence_survives_and_missing_artifact_is_not_complete(self):
        original = runner.BASE
        try:
            with tempfile.TemporaryDirectory() as directory:
                runner.BASE = Path(directory)
                (runner.BASE / 'protocol.json').write_text(json.dumps({
                    'completion_gates': {'independent_truth': False},
                    'model_policy': {'primary': 'luna'}}))
                artifact = runner.BASE / 'new-result.json'
                artifact.write_text('{}')
                prior = {
                    'completion_gates': {'independent_truth': True},
                    'evidence': {'new_experiment': {'edits': 12}},
                    'phases': [{'id': 'new_experiment', 'script': None,
                                'result': artifact.name, 'complete': True}],
                    'next_research': ['Keep the new hypothesis.']}
                (runner.BASE / 'CHECKPOINT.json').write_text(json.dumps(prior))
                first = runner.checkpoint()
                second = runner.checkpoint()
                self.assertEqual(second['evidence']['new_experiment'], {'edits': 12})
                self.assertEqual(first['next_research'], second['next_research'])
                self.assertEqual(sum(p['id'] == 'new_experiment' for p in second['phases']), 1)
                self.assertFalse(second['completion_gates']['independent_truth'])
                self.assertEqual(second['status'], 'in_progress')
                artifact.unlink()
                third = runner.checkpoint()
                self.assertFalse(next(p for p in third['phases'] if p['id'] == 'new_experiment')['complete'])
                self.assertEqual(third['evidence']['new_experiment'], {'edits': 12})
        finally:
            runner.BASE = original


if __name__ == '__main__':
    unittest.main()
