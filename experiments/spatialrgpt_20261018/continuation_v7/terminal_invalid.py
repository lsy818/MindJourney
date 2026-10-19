"""Finalize only an exhausted, strictly invalid final answer; no network or labels."""
import hashlib,json,os,time
from pathlib import Path

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put_new(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def classify(records,bodies,ctx,decode,model):
 assert ctx['kind']=='answer' and len(records)==len(bodies)==8
 for i,(r,j) in enumerate(zip(records,bodies),1):
  assert r['attempt']==i and r['payload_sha256']==ctx['payload_sha256']
  assert not r['accepted'] and r['transport_exit']==0 and r['http_status']==200 and r['error_type']=='ValueError'
  assert not j.get('error') and j['model']==model and j['provider']=='DeepInfra' and r['usage']==j.get('usage')
  assert len(j['choices'])==1 and j['choices'][0]['finish_reason']=='stop'
  msg=j['choices'][0]['message'];u=j['usage']
  assert not msg.get('reasoning') and not msg.get('reasoning_details') and (u.get('completion_tokens_details') or {}).get('reasoning_tokens',0)==0
  assert u['completion_tokens']<=8192
  try:decode(msg['content'],'answer',ctx['count'])
  except ValueError as e:assert str(e)=='final quantity/unit invalid'
  else:raise AssertionError('valid response may not be discarded')
 return True

def finalize(root,row,evidence):
 from api import decode,MODEL
 from recovery import validate_saved
 root=Path(root);trace=root/row['id'];out=root/'items'/(row['id']+'.json')
 assert not out.exists();failure=trace/'FAILED.json';f=json.loads(failure.read_text())
 assert f['error_type']=='APIError' and 'identical-payload budget exhausted' in f['traceback']
 calls=sorted((trace/'api').glob('call-*'));assert len(calls) in (3,5,7)
 receipts=[]
 for i,c in enumerate(calls):
  assert c.name=='call-%02d'%i
  ctx=json.loads((c/'context.json').read_text());assert digest(c/'request.json')==ctx['payload_sha256']
  aa=sorted(c.glob('attempt-*.json'),key=lambda p:int(p.stem.split('-')[-1]))
  starts=list(c.glob('ATTEMPT_STARTED-*.json'));assert len(starts)==len(aa)
  assert all(z.with_name(z.name.replace('ATTEMPT_STARTED-','attempt-')).exists() for z in starts)
  rr=[json.loads(a.read_text()) for a in aa];assert 1<=len(rr)<=8
  assert all(a.with_suffix('.body').exists() for a in aa)
  assert all(v['attempt']==n and v['payload_sha256']==ctx['payload_sha256'] for n,v in enumerate(rr,1))
  if i==len(calls)-1:classify(rr,[json.loads(a.with_suffix('.body').read_text()) for a in aa],ctx,decode,MODEL)
  else:
   assert ctx['kind']=='scores' and sum(bool(v['accepted']) for v in rr)==1 and rr[-1]['accepted']
   validate_saved(rr[-1],aa[-1].with_suffix('.body'),ctx['kind'],ctx['count'])
  receipts.extend(rr)
 files={str(p.relative_to(root)):digest(p) for p in trace.rglob('*') if p.is_file()}
 cert={'passed':True,'status':'invalid_answer','policy':'eight_failed_final_quantity_validations_zero_score_no_new_request','id':row['id'],'files':files,'failure_sha256':digest(failure),'payload_sha256':ctx['payload_sha256'],'attempts':8,'stopped_step_evidence':evidence,'unix':time.time()}
 certpath=root.parent/'CONTINUATION_V6'/'terminal'/ (row['id']+'.json');put_new(certpath,cert)
 item={'id':row['id'],'category':row['category'],'method':'MindJourney','prediction':'','final_answer':'','status':'invalid_answer','error':'strict_final_quantity_validation_exhausted','attempt':8,'latency_s':max(0,failure.stat().st_mtime-json.loads((trace/'STARTED.json').read_text())['unix']),'latency_kind':'trace_elapsed_at_failure','vlm_calls':len(calls),'tool_calls':len(list(trace.rglob('pred.mp4'))),'network_attempts':len(receipts),'selected_imaginations':[],'trace_path':str(trace),'usage_attempts':receipts,'terminal_receipt':str(certpath),'terminal_receipt_sha256':digest(certpath)}
 assert 3<=item['tool_calls']<=15
 put_new(out,item)
 return {'invalid_items':1,'attempts_preserved':len(receipts),'videos_preserved':item['tool_calls'],'new_api_calls':0,'new_gpu_generation':0,'terminal_sha256':digest(certpath)}
