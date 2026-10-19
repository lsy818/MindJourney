"""Run the original SVC beam search on answer-free SpatialRGPT inputs."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback
from types import SimpleNamespace
from common import atomic, sha, load_inputs, code_identity
from api import Client, MODEL
import recovery

ROOT=Path(__file__).resolve().parent
PROTOCOL='''The region labels identify the target objects in the original image.
Answer the original question using the original image as the reference view.
Return one final answer inside <answer>...</answer>.
For a distance or size, give one non-negative number and an explicit unit.
For a direction, give one integer clock hour from 1 to 12.
There is one original reference view. Generated images are predicted evidence,
not additional real observations. Region labels and masks identify targets only
in the original marked image; do not assume labels are preserved in generated
views. Identify corresponding objects visually and interpret every movement
relative to the original reference view. No ground-truth depth or scale is given.'''

def clean_choices(text):
    for old,new in [('Output the exact answer from the choices.','Answer the original open-ended question.'),
                    ('from the choices','with an open-ended quantitative answer'),
                    ('a question, and a set of answer choices','an open-ended question'),
                    ('excluding the wrong answers','resolving uncertainty'),
                    ('the exact answer choice','one final answer inside <answer>...</answer>'),
                    ("You should output a list of scores from 0 to 9, separated by ','. For example: Output: 3,5,2,9,0,1", 'Return the scores in the JSON format specified below.')]:
        text=text.replace(old,new)
    return text

class VLM:
    def __init__(self,client,category): self.client=client; self.category=category; self.curr_prompt=None
    def format_prompt(self,prompt_type,question,answer_choices,images,action_consequences=None,sys_prompt=None):
        from utils.prompt_formatting import format_spatial_vqa_prompt_scores, format_spatial_vqa_prompt_answer_scaling
        assert not answer_choices and len(images)==1
        if prompt_type=='prompt_scores':
            system,content=format_spatial_vqa_prompt_scores(question,[],images,action_consequences,sys_prompt)
            self.kind='scores';self.n=len(action_consequences)
            output=f'Return ONLY a JSON object with key "scores": exactly {self.n} integer scores from 0 to 9 in the existing imagined-image order. No extra keys.'
        elif prompt_type=='answer_scaling':
            system,content=format_spatial_vqa_prompt_answer_scaling(question,[],images,action_consequences)
            self.kind='answer';self.n=self.category
            output='Return ONLY a JSON object with key "answer". The string value must be a single <answer>...</answer> containing your final quantitative answer. No extra keys.'
        else: raise ValueError('unexpected prompt')
        content=[(clean_choices(c[0]),*c[1:]) for c in content if not c[0].startswith('Answer Choices:')]
        system=clean_choices(system)+'\n'+PROTOCOL+'\n'+output
        content.append((PROTOCOL+'\n'+output,))
        self.curr_prompt={'system':system,'content':content}
        return system,content
    def run_prompt(self,prompt_type,system,content):
        self.value=self.client.complete(system,content,self.kind,self.n)
        self.normalized=','.join(map(str,self.value)) if self.kind=='scores' else self.value
        return self.normalized

def stage_source(q,save_dir):
    import cv2
    import math
    def resize_to_short_side(img,target_short):
        h,w=img.shape[:2]
        if min(h,w)==target_short:return img
        scale=target_short/float(min(h,w))
        return cv2.resize(img,(int(math.ceil(w*scale)),int(math.ceil(h*scale))),interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_LINEAR)
    raw=cv2.imread(q['raw_image']); assert raw is not None
    staged=resize_to_short_side(raw,512); raw_staged=str(Path(save_dir)/'step_0/img_0.png')
    assert cv2.imwrite(raw_staged,staged)
    atomic(Path(save_dir)/'input_routing.json',{'raw_sha256':q['raw_sha256'],'marked_sha256':q['marked_sha256'],
           'svc_image':raw_staged,'svc_shape':list(staged.shape),'original_size':q['image_size'],
           'vlm_image':q['marked_image'],'marked_resize':'none; provider preprocessing uncontrolled',
           'generated_region_overlay':False,'cross_view_mapping':'native VLM visual correspondence only; no supplied geometry'})
    return raw_staged,[q['marked_image']]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--shared',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--keyfile',required=True);ap.add_argument('--mode',choices=['dev','full'],required=True)
    ap.add_argument('--recovery-baseline');ap.add_argument('--replay-check',action='store_true')
    ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1)
    a=ap.parse_args();os.umask(0o077)
    root=Path(a.output);root.mkdir(parents=True,exist_ok=True)
    if a.recovery_baseline:
        recovery.install(root,a.recovery_baseline,a.replay_check)
        global atomic
        atomic=recovery.guarded_atomic
    elif a.replay_check:raise ValueError('replay requires baseline')
    for name,digest in json.loads((ROOT/'FROZEN_SOURCE_SHA256.json').read_text()).items(): assert sha(ROOT/'frozen'/name)==digest
    inputs_receipt=Path(a.shared).parent/('INPUTS_PREFLIGHT_VERIFIED.json' if a.mode=='dev' else 'INPUTS_VERIFIED.json')
    assert json.loads(inputs_receipt.read_text())['passed']
    rows=load_inputs(a.shared)
    if a.mode=='dev':
        ids=json.loads((Path(a.shared)/'development_ids.json').read_text())
        if isinstance(ids,dict): ids=ids['development_ids']
        rows=[r for r in rows if r['id'] in ids];assert len(rows)==6
    else:
        gate=json.loads((root.parent/'PREFLIGHT_PASSED.json').read_text());assert gate['passed']
        assert gate['code_identity']==code_identity(), 'changed code requires new preflight'
        assert gate['manifest_sha256']==sha(Path(a.shared)/'inputs/spatialrgpt.jsonl')
        devroot=root.parent/'dev-v2'
        assert len(gate['item_sha256'])==6
        for qid,digest in gate['item_sha256'].items():assert sha(devroot/'items'/f'{qid}.json')==digest
        rows=[r for r in rows if r['id'] not in gate['item_sha256']]
        assert len(rows)==743
    rows=rows[a.shard::a.shards]
    if a.replay_check:rows=[r for r in rows if (root/r['id']/'STARTED.json').exists()]
    sys.path[:0]=[str(ROOT/'frozen'),str(ROOT/'frozen/pipelines'),str(ROOT/'frozen/stable_virtual_camera')]
    os.environ['WORLD_MODEL_TYPE']='svc';os.environ['MINDJOURNEY_MULTIIMAGE_ADAPTATION']='0'
    import cv2
    from pipeline_baseline import resize_to_short_side
    from stable_virtual_camera.demo import Model
    from utils import args as original
    from search import Search
    if a.recovery_baseline:
        import pipeline_svc_scaling_spatial_beam_search as original_search
        recovery.install_candidates(original_search)
    parser=argparse.ArgumentParser();original._get_svc_args(parser);original._get_pipeline_args(parser)
    opts=parser.parse_args(['--output_dir',str(root),'--input_dir',a.shared,'--question_type','None','--max_tries_gpt','5','--num_questions','749','--split','test'])
    settings=dict(vlm_model_name=MODEL,vlm_qa_model_name='None',max_images=1,num_frames=9,frame_interval=3,
                  sampling_interval_angle=9,sampling_interval_meter=.25,fixed_rotation_magnitudes=27,
                  fixed_forward_magnitudes=.75,max_turn_angle=60,max_forward_distance=1.5,max_steps_per_question=3,
                  num_top_candidates=18,num_beams=2,helpful_score_threshold=8,exploration_score_threshold=8,
                  max_inference_batch_size=1,task='img2trajvid_s-prob',replace_or_include_input=True,cfg=4.,
                  guider=1,L_short=576,num_targets=8,use_traj_prior=True,chunk_strategy='interp')
    for k,v in settings.items():setattr(opts,k,v)
    atomic(root/(f'settings-recovery-v5-{a.shard}.json' if a.recovery_baseline else f'settings-{a.shard}.json'),dict(arguments=vars(opts),mode=a.mode,shard=a.shard,shards=a.shards,code_identity=code_identity()))
    class Pipeline(Search):
        def __init__(self):
            self.replay_checked=0; self.model_args=opts; self.world_model_type='svc'; self.global_model=None if a.replay_check else Model()
        def _stage_source_images(self,q,save_dir):
            self.raw_staged,images=stage_source(q,save_dir)
            return images
        def _process_list(self,response):
            assert self.vlm.kind=='scores' and response==self.vlm.normalized
            return self.vlm.value
        def _take_action_with_world_model(self,*args,**kwargs):
            self.tool_calls+=len(args[2] if len(args)>2 else kwargs['action_lists'])
            return super()._take_action_with_world_model(*args,**kwargs)
        def _process_answer(self,response,question,*args,**kw):
            assert self.vlm.kind=='answer' and response==self.vlm.normalized
            return 'completed'
        def _dump_llm_interaction(self,save_dir,step,rank,question,response,result,actions,magnitude,**kw):
            name='final.json' if step is None else f'step_{step}/rank_{rank}.json'
            atomic(Path(save_dir)/name,{'response':response,'prompt':self.vlm.curr_prompt,'result':'unscored'})
        def save_results(self): pass
        def save_prediction(self,q,response,imaginations):
            value={'id':q['id'],'category':q['category'],'method':'MindJourney',
                   'prediction':response,'final_answer':response,'status':'ok','error':None,'attempt':1,
                   'latency_s':time.monotonic()-self.started,'vlm_calls':self.vlm.client.calls,
                   'tool_calls':self.tool_calls,
                   'network_attempts':len(self.vlm.client.receipts),'selected_imaginations':imaginations,
                   'trace_path':str(root/q['id']),'usage_attempts':self.vlm.client.receipts}
            if a.replay_check:
                saved=json.loads((root/'items'/f'{q["id"]}.json').read_text())
                for key in value:
                    if key!='latency_s':assert value[key]==saved[key], 'offline replay result differs'
                self.replay_checked+=1
            else:atomic(root/'items'/f'{q["id"]}.json',value)
    with (root/f'worker-{a.shard}.private.log').open('a',buffering=1) as log, contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        pipeline=Pipeline()
        for row in rows:
            qid=row['id'];done=root/'items'/f'{qid}.json'
            if done.exists() and not a.replay_check: continue
            trace=root/qid
            if trace.exists():
                assert recovery.BASELINE and str((trace/'STARTED.json').relative_to(root)) in recovery.BASELINE['files'], 'unreviewed incomplete trace'
            else:
                trace.mkdir()
                atomic(trace/'STARTED.json',{'id':qid,'unix':time.time(),'job':os.getenv('SLURM_JOB_ID')})
            started=time.monotonic()
            q=dict(row,database_idx=qid,eval_id=qid,question_type=row['category'],answer_choices=[],img_paths=[row['raw_image']])
            pipeline.questions=[q]; pipeline.started=started;pipeline.tool_calls=0;pipeline.vlm=VLM(Client(a.keyfile,trace/'api'),row['category'])
            pipeline.results={'skip_indices':[],'progress':{row['category']:{'correct':[],'wrong':[]}}}
            random.seed(10)
            try: pipeline.run()
            except recovery.RecoveryBoundary as exc:
                if not a.replay_check:raise
                assert str(exc)=='next network request', 'replay ended before exact request reconstruction'
                assert pipeline.replay_checked==len(list((root/'items').glob('*.json')))
                break
            except BaseException as exc:
                atomic(trace/('FAILED_RECOVERY_V5.json' if a.recovery_baseline else 'FAILED.json'),{'id':qid,'error_type':type(exc).__name__,'traceback':traceback.format_exc()})
                raise
    if a.replay_check:
        recovery.check_baseline()
        print(json.dumps({'offline_replay_passed':True,'checked_saved_items':pipeline.replay_checked,'network_calls':0,'gpu_calls':0}));return
    if a.recovery_baseline:recovery.check_baseline()
    atomic(root/f'WORKER_COMPLETE-{a.shard}.json',{'count':len(rows),'mode':a.mode})
    print(json.dumps({'worker_complete':a.shard,'count':len(rows),'mode':a.mode}))

if __name__=='__main__': main()
