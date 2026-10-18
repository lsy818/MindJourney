"""Submit once only after the stopped-job baseline and offline replay pass."""
import fcntl,json,subprocess,time
from pathlib import Path
from common import atomic,sha,code_identity

root=Path('/home/datasets/shiyang/mindjourney_spatialrgpt_20261018')
control=root/'RECOVERY_V3'
with (root/'submission.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    receipt=root/'DEV_V3_SUBMITTED.json'
    if receipt.exists():
        print(json.dumps({'already_submitted':True,'job_id':json.loads(receipt.read_text())['job_id']}))
    else:
        baseline=json.loads((control/'BASELINE.json').read_text())
        proof=json.loads((control/'OFFLINE_REPLAY.json').read_text())
        assert proof['passed'] and proof['baseline_sha256']==sha(control/'BASELINE.json')
        assert proof['code_identity']==code_identity()
        assert proof['summary']['checked_saved_items']==2
        assert proof['summary']['network_calls']==proof['summary']['gpu_calls']==0
        assert json.loads((root/'INPUTS_VERIFIED.json').read_text())['count']==749
        assert json.loads((control/'PROXY_ROUTE.json').read_text())['passed']
        p=subprocess.run(['sacct','-j','90197','-n','-P','--format=JobIDRaw,State'],capture_output=True,text=True,check=True)
        assert '90197|TIMEOUT' in p.stdout
        p=subprocess.run(['scontrol','listpids','90197','hkbugpusrv12'],capture_output=True,text=True)
        assert 'does not exist on node' in p.stdout+p.stderr
        p=subprocess.run(['sbatch','--parsable','dev.sbatch'],capture_output=True,text=True)
        if p.returncode:
            print(json.dumps({'submitted':False,'exit':p.returncode}));raise SystemExit(1)
        job=p.stdout.strip().split(';')[0];assert job.isdigit()
        atomic(receipt,{'job_id':job,'submitted_unix':time.time(),'code_identity':code_identity(),
            'batch_sha256':sha('dev.sbatch'),'baseline_sha256':sha(control/'BASELINE.json'),
            'offline_replay_sha256':sha(control/'OFFLINE_REPLAY.json'),'prior_job':'90197',
            'output':str(root/'dev-v2'),'allocation_hours':12})
        print(json.dumps({'submitted':True,'job_id':job,'completed_items_reused':2,'incomplete_items':4}))
