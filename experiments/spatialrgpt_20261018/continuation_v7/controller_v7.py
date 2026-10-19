"""Single-use continuation monitor. Existing healthy steps are never restarted."""
import fcntl,json,os,subprocess,sys,time,traceback
from pathlib import Path
C=Path('/home/comp/24482277/mindjourney_spatialrgpt_20261018_v5')
V=Path(__file__).resolve().parent
R=Path('/home/datasets/shiyang/mindjourney_spatialrgpt_20261018')
P=Path('/home/comp/24482277/mj_gpu_pool_20261019_v1')
D=V/'CONTROL'
sys.path.insert(0,str(C))
from common import load_inputs,code_identity,sha
from terminal_invalid import finalize,put_new

def read(p):return json.loads(p.read_text())
def status(phase,**kw):
 x=dict(phase=phase,unix=time.time(),saved_dev=len(list((R/'dev-v2/items').glob('*.json'))),saved_full=len(list((R/'full-v5/items').glob('*.json'))),**kw)
 for n in range(4):
  try:
   tmp=D/('status.%s.%s.tmp'%(os.getpid(),n));tmp.write_text(json.dumps(x)+'\n');os.replace(str(tmp),str(D/'status.json'));return
  except PermissionError:
   if n==3:raise
   time.sleep(1)
def launch(name,arg):
 assert not (P/'steps'/name).exists(), 'launch outcome uncertain; reconcile before retry'
 put_new(D/(name+'.dispatch.json'),{'name':name,'argument':arg,'unix':time.time()})
 cmd=['python3',str(P/'control.py'),'launch','--name',name,'--gpus','1','--cpus','6','--mem-gb','128','--cwd',str(V),'--','/bin/bash',str(V/'remaining.sh'),str(arg)]
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (D/(name+'.private.log')).write_bytes(p.stdout+p.stderr)
 assert p.returncode==0,'dispatch uncertain; do not repeat'
def inactive(step):
 p=subprocess.run(['squeue','-h','--steps','-j','90438','-o','%i'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
 assert p.returncode==0
 return '90438.'+str(step) not in p.stdout.split()
def main():
 os.umask(0o077);D.mkdir(exist_ok=True)
 lock=(D/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (D/'STARTED.json').exists()
 put_new(D/'STARTED.json',{'pid':os.getpid(),'unix':time.time(),'source_sha256':sha(__file__),'pool':'90438'})
 gate=read(R/'PREFLIGHT_PASSED.json');assert gate['passed'] and gate['count']==6 and gate['code_identity']==code_identity()
 assert not Path('/proc/233109').exists(),'old controller must be stopped'
 rows=[x for x in load_inputs(R/'shared') if x['id'] not in gate['item_sha256']];assert len(rows)==743
 names={i:'spatial-v5-full-'+str(i) for i in range(4)};generations={i:0 for i in range(4)}
 assert not Path('/proc/363656').exists(),'V6 controller must be stopped'
 old=P/'steps/spatial-v6-full-0-r1';ot=read(old/'task.json');ol=read(old/'launcher.json')
 assert ot['state']==ol['state']=='finished' and ot['exit_code']==ol['exit_code']==2 and inactive(ot['step_id'])
 for row in rows[0::4]:
  assert not (R/'full-v5'/row['id']).exists() or (R/'full-v5/items'/(row['id']+'.json')).exists(), 'incomplete trace prevents startup repair'
 names[0]='spatial-v7-full-0-r1';generations[0]=1
 launch(names[0],0)
 while True:
  done=0
  for i in range(4):
   directory=P/'steps'/names[i]
   lf=directory/'launcher.json';tf=directory/'task.json'
   if not lf.exists() or not tf.exists():continue
   l,t=read(lf),read(tf)
   if l['state']!='finished' or t['state']!='finished':continue
   assert inactive(t['step_id']),'finished receipt but live step'
   if l['exit_code']==0 and t['exit_code']==0:done+=1;continue
   subset=rows[i::4];missing=[x for x in subset if not (R/'full-v5/items'/(x['id']+'.json')).exists()]
   failed=[x for x in missing if (R/'full-v5'/x['id']/'FAILED.json').exists()]
   assert len(failed)==1,'not exactly one reviewed terminal failure; no automatic replay'
   row=failed[0]
   assert all(not (R/'full-v5'/x['id']).exists() for x in missing if x['id']!=row['id']),'other incomplete traces require review'
   evidence={'name':names[i],'step_id':t['step_id'],'launcher_sha256':sha(lf),'task_sha256':sha(tf),'squeue_step_absent':True}
   result=finalize(R/'full-v5',row,evidence)
   put_new(D/('terminal-%s-%s.json'%(i,generations[i])),result)
   generations[i]+=1;name='spatial-v7-full-%s-r%s'%(i,generations[i])
   launch(name,i);names[i]=name
  status('full_running',steps=names,finished_shards=done,invalid_items=len(list((R/'CONTINUATION_V6/terminal').glob('*.json'))))
  if done==4:break
  time.sleep(30)
 assert len(list((R/'full-v5/items').glob('*.json')))==743
 name='spatial-v7-audit-full';launch(name,'audit')
 while True:
  status('final_audit',steps=names)
  f=P/'steps'/name/'launcher.json'
  if f.exists():
   l=read(f)
   if l['state']=='finished':assert l['exit_code']==0,'final audit failed';break
  time.sleep(30)
 assert read(R/'FINAL_VERIFIED.json')['passed'] and read(R/'FINAL_SUMMARY.json')['total']==749
 status('finished',total=749)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  (D/'failure.private.log').write_text(traceback.format_exc());status('failed',error_type=type(e).__name__);sys.exit(1)
