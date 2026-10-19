"""New single-use wrapper; preserve v5 inference source and completed items."""
import hashlib,json,os,sys
from pathlib import Path
C=Path('/home/comp/24482277/mindjourney_spatialrgpt_20261018_v5')
R=Path('/home/datasets/shiyang/mindjourney_spatialrgpt_20261018')
sys.path.insert(0,str(C))
import common,worker
os.umask(0o077)
shard=int(sys.argv[1]);assert 0<=shard<4
root=R/'full-v5';gate=json.loads((R/'PREFLIGHT_PASSED.json').read_text());assert common.code_identity()==gate['code_identity']
rows=[x for x in common.load_inputs(R/'shared') if x['id'] not in gate['item_sha256']][shard::4]
for row in rows:
 trace=root/row['id'];item=root/'items'/(row['id']+'.json')
 assert not trace.exists() or item.exists(), 'unreviewed incomplete trace; no replay allowed'
 if item.exists():
  x=json.loads(item.read_text())
  if x['status']=='invalid_answer':
   cert=Path(x['terminal_receipt']);assert common.sha(cert)==x['terminal_receipt_sha256']
   for name,d in json.loads(cert.read_text())['files'].items():assert common.sha(root/name)==d
original=worker.atomic
def preserve(p,value):
 p=Path(p)
 if p.exists():
  assert json.loads(p.read_text())==json.loads(json.dumps(value)), 'existing artifact differs'
  return
 original(p,value)
worker.atomic=preserve
sys.argv=['worker.py','--shared',str(R/'shared'),'--output',str(root),'--keyfile','/home/comp/24482277/.config/mindjourney-spatialrgpt-20261018/openrouter.key','--mode','full','--shard',str(shard),'--shards','4']
worker.main()
