import ast
import json
from pathlib import Path
import unittest
from api import decode, MODEL
from worker import VLM, PROTOCOL, stage_source
from vendor.compute_score import compute_score_spatialrgpt

ROOT=Path(__file__).parent

class Contract(unittest.TestCase):
    def test_svc_raw_filename_and_vlm_marked_isolation(self):
        import tempfile
        import numpy as np
        from PIL import Image
        from common import sha
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'step_0').mkdir()
            Image.new('RGB',(512,512),'red').save(root/'raw.png')
            Image.new('RGB',(512,512),'blue').save(root/'marked.png')
            row={'raw_image':str(root/'raw.png'),'marked_image':str(root/'marked.png'),
                 'raw_sha256':sha(root/'raw.png'),'marked_sha256':sha(root/'marked.png'),'image_size':[512,512]}
            raw,vlm=stage_source(row,root)
            # The frozen SVC demo reads this exact path regardless of data_path.
            expected=root/'step_0'/'img_0.png'
            self.assertEqual(Path(raw),expected)
            self.assertTrue(np.array_equal(np.asarray(Image.open(expected)),np.asarray(Image.open(root/'raw.png'))))
            self.assertEqual(vlm,[str(root/'marked.png')])
            self.assertFalse(np.array_equal(np.asarray(Image.open(expected)),np.asarray(Image.open(vlm[0]))))
    def test_model_exact(self):
        self.assertEqual(MODEL,'deepseek/deepseek-v4.1-flash')
    def test_strict_scores(self):
        self.assertEqual(decode('{"scores":[0,9]}','scores',2),[0,9])
        for s in ['{"scores":[true,9]}','{"scores":[1]}','{"scores":[1,10]}','{"scores":[1,2],"x":0}','{"scores":[1,2],"scores":[1,2]}']:
            with self.assertRaises(ValueError):decode(s,'scores',2)
    def test_metric_explicit_one_quantity(self):
        self.assertEqual(decode('{"answer":"<answer>80 cm</answer>"}','answer','width_data'),'<answer>80 cm</answer>')
        for s in ['0.8','-1 m','1 m or 2 m','nan m','<answer>1 m</answer>']:
            with self.assertRaises(ValueError):decode(json.dumps({'answer':'<answer>'+s+'</answer>'}),'answer','width_data')
    def test_clock_range(self):
        for n in range(1,13):decode(json.dumps({'answer':f"<answer>{n} o'clock</answer>"}),'answer','direction')
        for n in [0,13,1.5]:
            with self.assertRaises(ValueError):decode(json.dumps({'answer':f'<answer>{n}</answer>'}),'answer','direction')
    def test_reference_scoring(self):
        for p in ['75 cm','125 cm']:
            self.assertEqual(compute_score_spatialrgpt('<answer>'+p+'</answer>','1 m','width_data'),1)
        self.assertEqual(compute_score_spatialrgpt('<answer>126 cm</answer>','1 m','width_data'),0)
        self.assertEqual(compute_score_spatialrgpt("<answer>12 o'clock</answer>","1 o'clock",'direction'),1)
        self.assertEqual(compute_score_spatialrgpt('',"1 o'clock",'direction'),0)
    def test_search_core_unchanged(self):
        source=(ROOT/'frozen/pipelines/pipeline_svc_scaling_spatial_beam_search.py').read_text()
        cls=next(x for x in ast.parse(source).body if isinstance(x,ast.ClassDef) and x.name=='SpatialVQAPipelineSVC')
        fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='run')
        original='\n'.join(source.splitlines()[fn.lineno-1:fn.end_lineno])
        adapted=(ROOT/'search.py').read_text()
        first='            response, result, action_list, magnitude ='
        last='            # Persist raw exchange'
        self.assertEqual(original[original.index(first):original.index(last)],adapted[adapted.index(first):adapted.index(last)])
    def test_no_labels_in_inference(self):
        tree=ast.parse((ROOT/'worker.py').read_text())
        literals=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        self.assertFalse(any('labels.jsonl' in s or 'conversations' in s or 'ground_truth' in s for s in literals))

if __name__=='__main__': unittest.main()
