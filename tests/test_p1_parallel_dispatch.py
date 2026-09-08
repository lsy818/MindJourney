import importlib.util
import json
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('dispatch', Path(__file__).parents[1] / 'scripts/p1_parallel_dispatch.py')
dispatch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dispatch)


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mock = patch.object(dispatch, 'ROOT', self.root)
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.addCleanup(self.tmp.cleanup)

    def fixture(self, plan):
        dataset, model, accelerator, cap, chunks, log = plan
        name = 'mj-p1-{}-{}-{}-fast-r8-20260908'.format(dataset, model, accelerator)
        run = self.root / name
        run.mkdir()
        manifest = dict(run_id=name, source_sha256=dispatch.SOURCE, dtype='bfloat16', max_model_len='65536', accelerator=accelerator, num_chunks=str(chunks), tensor_parallel_size='2', total_gpus='3')
        (run / 'launch_manifest.txt').write_text('\n'.join(k+'='+v for k,v in manifest.items()))
        parent = run / ('results_spatial_beam_search_qc'+str(chunks))
        first = parent / 'question_chunk_0'
        first.mkdir(parents=True)
        (first / 'results.json').write_text(json.dumps(dict(progress={'test': {'correct':[1]}}, skip_indices=[])))
        exports = dict(P1_RUN_ID=name, P1_REPO_DIR=str(dispatch.REPO), P1_EXPECTED_SOURCE_SHA256=dispatch.SOURCE)
        cmd = ['sbatch', '--array=0%1', '--gres=gpu:'+accelerator+(':'+('3' if accelerator=='h20' else '2')), '--export='+','.join(k+'='+v for k,v in exports.items()), '--exclude=hkbugpudgx01,hkbugpusrv07,hkbugpusrv08', str(dispatch.REPO / 'scripts/p1_array.sbatch')]
        (self.root / log).write_text('command='+shlex.join(cmd))
        return parent

    def job(self, index, array='100', state='RUNNING', plan=None):
        plan = plan or dispatch.PLANS[0]
        return dict(id=array+'_'+str(index), name='mj-p1-{}-{}-array'.format(plan[0],plan[1]), state=state, reason='test')

    def test_combined_arrays_and_pending_count(self):
        self.fixture(dispatch.PLANS[0])
        record, cmd = dispatch.prepare(dispatch.PLANS[0], [self.job(0), self.job(1,'101','PENDING')],10)
        self.assertEqual(record['new_indices'],[2])
        self.assertIn('--array=2%1',cmd)

    def test_full_combined_cap_no_submission(self):
        self.fixture(dispatch.PLANS[0])
        record, cmd = dispatch.prepare(dispatch.PLANS[0],[self.job(i,str(i+100)) for i in range(3)],10)
        self.assertIsNone(cmd)

    def test_completed_excluded(self):
        parent = self.fixture(dispatch.PLANS[0])
        (parent/'question_chunk_0/COMPLETE').touch()
        record, cmd = dispatch.prepare(dispatch.PLANS[0],[],10)
        self.assertEqual(record['new_indices'],[1,2,3])

    def test_global_submit_limit(self):
        self.fixture(dispatch.PLANS[0])
        jobs=[dict(id=str(i),name='unrelated',state='PENDING') for i in range(9)]
        record, cmd=dispatch.prepare(dispatch.PLANS[0],jobs,10)
        self.assertEqual(record['new_indices'],[0])

    def test_duplicate_array_index_rejected(self):
        self.fixture(dispatch.PLANS[0])
        with self.assertRaises(AssertionError):
            dispatch.prepare(dispatch.PLANS[0],[self.job(0),self.job(0,'101')],10)

    def test_72b_explicit_budget(self):
        plan=dispatch.PLANS[1]
        self.fixture(plan)
        record,cmd=dispatch.prepare(plan,[self.job(0,plan=plan)],10)
        self.assertIn('P1_GPU_MEMORY_UTILIZATION=0.93',next(x for x in cmd if x.startswith('--export=')))
        self.assertIn('--gres=gpu:h20:3',cmd)
        self.assertEqual(record['new_indices'],[1])


if __name__ == '__main__':
    unittest.main()
