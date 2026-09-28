"""Real subprocess tests of scheduling, persistence and failure isolation."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import fcntl

SPEC = importlib.util.spec_from_file_location('experiment_queue', Path(__file__).resolve().parents[1] / 'scripts/experiment_queue.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def command(self, key, code=None, deps=(), resource='cpu', outputs=None, inputs=(), timeout=5):
        return dict(id=key, kind='command', resource=resource, deps=list(deps), inputs=list(inputs),
                    outputs=outputs or [key+'.json'], timeout_seconds=timeout,
                    argv=['{python}', '-c', code or f"from pathlib import Path; Path('{key}.json').write_text('{{}}')"])

    def queue(self, jobs):
        manifest = self.root / 'queue.json'
        manifest.write_text(json.dumps({'resources': {'cpu': 1, 'io': 2, 'vlm': 1}, 'jobs': jobs}))
        return mod.Queue(self.root, manifest, self.root/'state.json')

    def test_concurrent_lanes_then_dependency_and_idempotent_resume(self):
        # cpu cannot finish without io's marker: sequential execution would time out.
        cpu = "import time; from pathlib import Path; Path('cpu-start').touch();\nwhile not Path('io-start').exists(): time.sleep(.01)\nPath('cpu.json').write_text('{}')"
        io = "import time; from pathlib import Path; Path('io-start').touch();\nwhile not Path('cpu-start').exists(): time.sleep(.01)\nPath('io.json').write_text('{}')"
        q = self.queue([self.command('cpu', cpu), self.command('io', io, resource='io'), self.command('join', deps=['cpu','io'])])
        with q.lock():
            first = q.run(10)
            times = {k: v['started_at'] for k,v in q.state['jobs'].items()}
            second = q.run(10)
        self.assertEqual(set(first['jobs'].values()), {'completed'})
        self.assertEqual(first, second)
        self.assertEqual(times, {k: v['started_at'] for k,v in q.state['jobs'].items()})
        self.assertGreaterEqual(q.state['jobs']['join']['started_at'], max(q.state['jobs'][x]['ended_at'] for x in ['cpu','io']))

    def test_failure_blocks_only_dependents_and_requires_evidence(self):
        q = self.queue([self.command('bad','raise SystemExit(2)'), self.command('child',deps=['bad']),
                        self.command('independent'), self.command('missing','pass'),
                        self.command('invalid',"from pathlib import Path; Path('invalid.json').write_text('not-json')")])
        with q.lock(): r=q.run(10)
        self.assertEqual(r['jobs'], {'bad':'failed','child':'pending','independent':'completed','missing':'failed','invalid':'failed'})
        self.assertEqual(r['waiting']['child']['dependencies'], ['bad'])

    def test_input_and_output_mutation_invalidates_downstream_without_rerun(self):
        (self.root/'input').write_text('original')
        q=self.queue([self.command('parent',inputs=['input']), self.command('child',deps=['parent'])])
        with q.lock(): q.run(10)
        (self.root/'input').write_text('changed')
        with q.lock(): r=q.run(10)
        self.assertEqual(r['jobs'],{'parent':'stale','child':'stale'})
        q=self.queue([self.command('output')])
        with q.lock(): q.run(10)
        (self.root/'output.json').write_text('{"modified":true}')
        with q.lock(): r=q.run(10)
        self.assertEqual(r['jobs']['output'],'stale')

    def test_external_claims_are_exclusive_and_need_artifact_and_token(self):
        jobs=[dict(id=k,kind='external',resource='vlm',deps=[],inputs=[],outputs=[k+'.json']) for k in ['reader','other']]
        q=self.queue(jobs)
        with q.lock():
            q.run(10)
            claim=q.claim('reader','luna/real-agent-id')
            with self.assertRaises(ValueError): q.claim('other','other-agent')
            with self.assertRaises(ValueError): q.complete('reader','wrong-token')
            (self.root/'reader.json').write_text('{"test_fixture":true}')
            self.assertEqual(q.complete('reader',claim['token'])['status'],'completed')
            with self.assertRaises(ValueError): q.complete('reader',claim['token'])
            self.assertEqual(q.claim('other','second')['status'],'claimed')

    def test_stale_external_claim_keeps_resource_reserved(self):
        (self.root/'image').write_text('original')
        jobs=[dict(id=k,kind='external',resource='vlm',deps=[],inputs=['image'],outputs=[k+'.json']) for k in ['reader','other']]
        q=self.queue(jobs)
        with q.lock(): q.claim('reader','agent')
        (self.root/'image').write_text('changed')
        with q.lock():
            q.reconcile()
            self.assertEqual(q.state['jobs']['reader']['status'],'stale')
            with self.assertRaises(ValueError): q.claim('other','agent2')

    def test_resume_unknown_running_does_not_spawn_duplicate(self):
        q=self.queue([self.command('unknown'), self.command('io',resource='io')])
        q.state['jobs']['unknown']={'status':'running','pid':999999}
        q.save()
        with q.lock(): r=q.run(10)
        self.assertEqual(r['jobs']['unknown'],'interrupted')
        self.assertEqual(r['jobs']['io'],'completed')
        self.assertFalse((self.root/'unknown.json').exists())

    def test_timeout_and_existing_unowned_output(self):
        (self.root/'exists.json').write_text('{"preserve":true}')
        q=self.queue([self.command('timeout','import time; time.sleep(20)',timeout=.1),self.command('exists'),self.command('good')])
        with q.lock(): r=q.run(10)
        self.assertEqual(r['jobs'],{'timeout':'failed','exists':'blocked','good':'completed'})
        self.assertEqual(json.loads((self.root/'exists.json').read_text()),{'preserve':True})

    def test_shared_legacy_lock_and_invalid_dag(self):
        q=self.queue([self.command('one')])
        with q.lock():
            other=self.queue([self.command('one')])
            with self.assertRaises(BlockingIOError):
                with other.lock(): pass
        with self.assertRaises(ValueError): self.queue([self.command('a',deps=['b']),self.command('b',deps=['a'])])
        with self.assertRaises(ValueError): self.queue([self.command('escape',outputs=['../escape'])])
        with self.assertRaises(ValueError): self.queue([self.command('a'),self.command('a')])

    def test_deadline_does_not_admit_more_work(self):
        q=self.queue([self.command('slow','import time; time.sleep(20)'),self.command('next')])
        with q.lock(): r=q.run(.1)
        self.assertEqual(r['jobs'],{'slow':'failed','next':'pending'})


if __name__ == '__main__':
    import argparse,time
    p=argparse.ArgumentParser(); p.add_argument('--report'); args=p.parse_args()
    start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(QueueTest))
    if args.report:
        mod.atomic_json(Path(args.report), {'tests_run':result.testsRun,'failures':len(result.failures),
            'errors':len(result.errors),'successful':result.wasSuccessful(),'seconds':time.monotonic()-start,
            'scope':'orchestrator subprocess tests, not OCR or scientific success'})
    sys.exit(not result.wasSuccessful())
