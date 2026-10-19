"""Version 5: explicit, hash-checked replay of a stopped allocation; no blind restart."""
import hashlib
import json
from pathlib import Path
from common import sha, atomic

BASELINE=None
ROOT=None
DRY=False
class RecoveryBoundary(RuntimeError): pass

def check_baseline():
    assert BASELINE and ROOT
    for name,digest in BASELINE['files'].items():
        assert sha(ROOT/name)==digest, 'inherited artifact changed'

def install(root,baseline,dry=False):
    global BASELINE,ROOT,DRY
    ROOT=Path(root);BASELINE=json.loads(Path(baseline).read_text());DRY=dry
    assert BASELINE['passed'] and BASELINE['slurm_node_job_absent']
    assert BASELINE['output']==str(ROOT)
    check_baseline()
    import cv2
    original=cv2.imwrite
    def immutable_image(path,array,*args,**kwargs):
        p=Path(path)
        if p.exists() and p.is_relative_to(ROOT):
            ok,encoded=cv2.imencode(p.suffix,array,*args,**kwargs)
            assert ok and hashlib.sha256(encoded.tobytes()).hexdigest()==sha(p), 'replayed image mismatch'
            return True
        if DRY:raise RecoveryBoundary('missing image')
        return original(path,array,*args,**kwargs)
    cv2.imwrite=immutable_image

def guarded_atomic(path,value):
    p=Path(path)
    if BASELINE and p.exists() and p.is_relative_to(ROOT):
        assert json.loads(p.read_text())==json.loads(json.dumps(value)), 'replayed metadata mismatch'
        return
    if DRY:return
    atomic(p,value)

def validate_saved(record,body,kind,n):
    from api import decode,MODEL
    assert record['accepted'] and record['http_status']==200 and record['transport_exit']==0
    j=json.loads(body.read_text())
    assert j['model']==MODEL and j['provider']=='DeepInfra' and j.get('usage')==record['usage']
    assert len(j['choices'])==1
    c=j['choices'][0];assert c['finish_reason']=='stop'
    assert not c['message'].get('reasoning') and not c['message'].get('reasoning_details')
    usage=j['usage'];assert usage['completion_tokens']<=8192
    assert (usage.get('completion_tokens_details') or {}).get('reasoning_tokens',0)==0
    return decode(c['message']['content'],kind,n)

def restore_call(folder,encoded,context,kind,n):
    if not folder.exists():return [],False,None
    assert BASELINE is not None, 'existing call requires reviewed recovery baseline'
    assert str((folder/'request.json').relative_to(ROOT)) in BASELINE['files']
    assert (folder/'request.json').read_bytes()==encoded, 'reconstructed payload differs'
    assert json.loads((folder/'context.json').read_text())==context, 'reconstructed context differs'
    receipts=[json.loads(p.read_text()) for p in sorted(folder.glob('attempt-*.json'),key=lambda p:int(p.stem.split('-')[-1]))]
    digest=hashlib.sha256(encoded).hexdigest()
    reserved=BASELINE['reserved_attempts'].get(str(folder.relative_to(ROOT)),len(receipts))
    assert len(receipts)<=reserved<=attempt_limit(digest)
    for i,r in enumerate(receipts,1):
        assert r['attempt']==i and r['payload_sha256']==digest
        if r['accepted']:
            assert i==len(receipts)==reserved
            return receipts,True,validate_saved(r,folder/f'attempt-{i}.body',kind,n)
        assert r['http_status'] not in (400,401,402,403) and r.get('error_type')!='APIError'
    # This reviewed baseline has one request interrupted by Slurm with no body.
    for i in range(len(receipts)+1,reserved+1):
        assert not (folder/f'attempt-{i}.body').exists(), 'unreceipted body needs private review'
        r={'attempt':i,'http_status':0,'transport_exit':-15,'latency_s':None,
           'payload_sha256':digest,'accepted':False,'usage':None,'model':None,'provider':None,
           'error_type':'InterruptedUnknownUsage','prior_job':BASELINE['prior_job']}
        if not DRY:atomic(folder/f'attempt-{i}.json',r)
        receipts.append(r)
    return receipts,False,None

def install_candidates(module):
    import numpy as np
    import cv2
    original=module._run_one_candidate
    def candidate(action_list,magnitude,img_path,step_dir,folder,opts,model,forward_size,turn_size):
        out=Path(step_dir)/folder;pred=out/'pred.mp4'
        if pred.exists():
            assert BASELINE and str(pred.relative_to(ROOT)) in BASELINE['files']
            assert sha(pred)==BASELINE['files'][str(pred.relative_to(ROOT))]
            _,expected=module._build_trajectory(action_list,np.zeros(3,dtype=float),np.array([np.radians(-20.),0.,0.]),forward_size,turn_size)
            assert json.loads((out/'episode.json').read_text())==json.loads(json.dumps(expected))
            cap=cv2.VideoCapture(str(pred));assert cap.isOpened();count=0
            while True:
                ok,_=cap.read()
                if not ok:break
                count+=1
            cap.release();assert count==16, 'incomplete inherited video'
            return
        if out.exists():raise RecoveryBoundary('partial candidate requires separate review')
        if DRY:raise RecoveryBoundary('new candidate boundary')
        return original(action_list,magnitude,img_path,step_dir,folder,opts,model,forward_size,turn_size)
    module._run_one_candidate=candidate


EXHAUSTED_DIGEST='392bda63089fcaf3e46ddff0680ff8eb44d1fbbd8aa7edef8a60a6f8653efd92'
def attempt_limit(digest):
    # The October 19 human instruction authorizes repair then continuation.
    # Only this exhausted request receives one controlled attempt, number9.
    # Its original eight attempts remain immutable, counted, and auditable.
    if digest!=EXHAUSTED_DIGEST or BASELINE is None:return 8
    policy=BASELINE.get('continuation_policy',{})
    assert policy.get('payload_sha256')==digest and policy.get('total_limit')==9
    assert policy.get('prior_attempts')==8 and policy.get('additional_attempts')==1
    assert policy.get('authorization')=='human_20261019_repair_then_resume'
    return 9
