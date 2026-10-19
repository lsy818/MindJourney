"""Single-use orchestration inside pool90438; never retries a failed worker."""
import fcntl,json,os,subprocess,sys,time
from pathlib import Path
R=Path('/home/datasets/shiyang/mindjourney_spatialrgpt_20261018')
P=Path('/home/comp/24482277/mj_gpu_pool_20261019_v1')
C=Path('/home/comp/24482277/mindjourney_spatialrgpt_20261018_v5')
D=R/'POOL_CONTROLLER_V5'
def read(p):return json.loads(p.read_text())
def status(phase,**kw):
 t=D/'status.tmp';t.write_text(json.dumps(dict(phase=phase,unix=time.time(),**kw))+'\n');t.replace(D/'status.json')
def launch(name,script,arg):
 assert not (P/'steps'/name).exists(),'step already exists; manual reconciliation required'
 p=subprocess.run(['python3',str(P/'control.py'),'launch','--name',name,'--gpus','1','--cpus','6','--mem-gb','128','--cwd',str(C),'--','/bin/bash',str(C/script),str(arg)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (D/(name+'.private.log')).write_bytes(p.stdout+p.stderr)
 assert p.returncode==0,'launch failed; no automatic resubmission'
def done(names):
 for n in names:
  f=P/'steps'/n/'launcher.json'
  if not f.exists():return False
  v=read(f)
  if v['state']!='finished':return False
  assert v['exit_code']==0,'worker failed; preserve all artifacts and inspect privately'
 return True
def wait(names,phase):
 while not done(names):
  status(phase,items=len(list((R/'dev-v2/items').glob('*.json'))),full_items=len(list((R/'full-v5/items').glob('*.json'))))
  time.sleep(30)
os.umask(0o077);D.mkdir(exist_ok=True)
with (D/'controller.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (D/'STARTED.json').exists(),'controller is single-use'
 (D/'STARTED.json').write_text(json.dumps({'pid':os.getpid(),'unix':time.time(),'pool_job':'90438'})+'\n')
 try:
  assert read(R/'INPUTS_VERIFIED.json')['count']==749
  assert read(R/'RECOVERY_V5/TRANSPORT_PASSED.json')['passed']
  assert read(R/'RECOVERY_V5/OFFLINE_REPLAY.json')['passed']
  status('controlled_resume')
  launch('spatial-v5-dev-2','pool_dev_v5.sh',2)
  baseline=read(R/'RECOVERY_V5/BASELINE.json');digest=baseline['continuation_policy']['payload_sha256']
  target=None
  for call in (R/'dev-v2').glob('*/api/call-*'):
   if read(call/'context.json')['payload_sha256']==digest:target=call
  assert target is not None
  while not (target/'attempt-9.json').exists():
   assert not done(['spatial-v5-dev-2']),'controlled worker exited without verification receipt'
   time.sleep(15)
  receipt=read(target/'attempt-9.json')
  assert receipt['accepted'] and receipt['payload_sha256']==digest and receipt['attempt']==9,'controlled continuation failed; do not launch other workers'
  status('transport_real_request_passed')
  for i in (0,1,3):launch('spatial-v5-dev-'+str(i),'pool_dev_v5.sh',i)
  wait(['spatial-v5-dev-'+str(i) for i in range(4)],'preflight_running')
  launch('spatial-v5-audit-dev','pool_full_v5.sh','audit-dev');wait(['spatial-v5-audit-dev'],'preflight_audit')
  gate=read(R/'PREFLIGHT_PASSED.json');assert gate['passed'] and gate['count']==6
  for i in range(4):launch('spatial-v5-full-'+str(i),'pool_full_v5.sh',i)
  wait(['spatial-v5-full-'+str(i) for i in range(4)],'full_running')
  launch('spatial-v5-audit-full','pool_full_v5.sh','audit-full');wait(['spatial-v5-audit-full'],'final_audit')
  assert read(R/'FINAL_VERIFIED.json')['passed'] and read(R/'FINAL_SUMMARY.json')['total']==749
  status('finished',total=749)
 except BaseException as e:
  import traceback
  (D/'failure.private.log').write_text(traceback.format_exc())
  status('failed',error_type=type(e).__name__)
  sys.exit(1)
