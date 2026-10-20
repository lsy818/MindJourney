"""Seven user-authorized answer-only repairs. Never import GPU/search/worker code."""
import copy, fcntl, hashlib, json, math, os, re, subprocess, sys, time, traceback
from pathlib import Path

C=Path('/home/comp/24482277/mindjourney_spatialrgpt_20261018_v5')
R=Path('/home/datasets/shiyang/mindjourney_spatialrgpt_20261018')
D=R/'ANSWER_REPAIR_V1_20261020'
sys.path.insert(0,str(C))
from api import decode, MODEL, PROVIDER
from common import sha, atomic, code_identity

SUFFIX='\n\nOutput-format clarification for this length question: estimate the physical length from the supplied images and original question, and express it in meters. Return exactly one JSON object with the key "answer", whose value contains <answer>, one finite non-negative decimal number, a space followed by the literal unit m, and </answer>. Do not return percentages, pixels, image-relative lengths, person counts, generic "unit", or explanations. Do not merely relabel a relative quantity as meters. Keep the original question and reference view unchanged.'
PATTERN=r'^<answer>[0-9]+(?:\.[0-9]+)? m</answer>$'
ROUTE='openrouter.ai:443:127.0.0.1:18443'

def revised(payload):
    p=copy.deepcopy(payload)
    assert p['messages'][0]['role']=='system' and isinstance(p['messages'][0]['content'],str)
    p['messages'][0]['content']+=SUFFIX
    prop=p['response_format']['json_schema']['schema']['properties']['answer']
    prop.update(pattern=PATTERN,description='One finite non-negative physical length in meters inside literal answer tags, with a space before m.')
    return p

def validate_body(j,category):
    assert j.get('model')==MODEL and j.get('provider')=='DeepInfra' and not j.get('error')
    choices=j['choices'];assert len(choices)==1 and choices[0]['finish_reason']=='stop'
    msg=choices[0]['message'];u=j['usage']
    assert not msg.get('reasoning') and not msg.get('reasoning_details')
    assert not (u.get('completion_tokens_details') or {}).get('reasoning_tokens',0)
    assert 0<=u['completion_tokens']<=8192
    ans=decode(msg['content'],'answer',category)
    assert re.fullmatch(PATTERN,ans) and math.isfinite(float(ans[8:-9].split()[0]))
    return ans

def prepare():
    os.umask(0o077);D.mkdir(exist_ok=False)
    old=json.loads((R/'FINAL_VERIFIED.json').read_text())
    assert old['passed'] and old['count']==749 and old['code_identity']==code_identity()
    selected=[]
    for ident,root in old['item_sources'].items():
        f=Path(root)/'items'/(ident+'.json');assert sha(f)==old['item_sha256'][ident]
        x=json.loads(f.read_text())
        if x['status']=='ok':
            assert decode(json.dumps({'answer':x['final_answer']}),'answer',x['category'])==x['final_answer']
            continue
        assert x['status']=='invalid_answer' and x['category'] in ('width_data','height_data')
        calls=sorted((Path(root)/ident/'api').glob('call-*'));call=calls[-1]
        ctx=json.loads((call/'context.json').read_text());assert ctx['kind']=='answer'
        assert len(list(call.glob('attempt-*.json')))==8
        folder=D/'requests'/ident;folder.mkdir(parents=True)
        original=json.loads((call/'request.json').read_text());payload=revised(original)
        atomic(folder/'request.json',payload)
        atomic(folder/'source.json',{'id':ident,'category':x['category'],'original_call':str(call),'original_payload_sha256':sha(call/'request.json'),'original_item_sha256':sha(f),'request_sha256':sha(folder/'request.json'),'images':ctx['images']})
        selected.append(ident)
    assert len(selected)==7
    atomic(D/'PLAN.json',{'scope':'seven_invalid_final_answers_only','authorized_date':'2026-10-20','selected_ids':selected,'old_receipt_sha256':sha(R/'FINAL_VERIFIED.json'),'old_summary_sha256':sha(R/'FINAL_SUMMARY.json'),'frozen_code_identity':code_identity(),'format_instruction':SUFFIX,'pattern':PATTERN,'max_attempts_per_new_payload':8,'old_attempts_preserved':56,'gpu_generation':False,'original_valid_count':742})
    print(json.dumps({'prepared':7,'old_valid_reparsed':742,'new_api_requests':0,'gpu_generation':0}))

def run():
    os.umask(0o077)
    lock=open(D/'run.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (D/'STARTED.json').exists()
    plan=json.loads((D/'PLAN.json').read_text())
    assert sha(R/'FINAL_VERIFIED.json')==plan['old_receipt_sha256'] and code_identity()==plan['frozen_code_identity']
    keyfile=Path('/home/comp/24482277/.config/mindjourney-spatialrgpt-20261018/openrouter.key')
    assert not keyfile.stat().st_mode&0o077;key=keyfile.read_text().strip()
    atomic(D/'STARTED.json',{'pid':os.getpid(),'unix':time.time(),'script_sha256':sha(Path(__file__))})
    atomic(D/'status.json',{'phase':'running','accepted':0,'unix':time.time()})
    completed=0
    try:
        for ident in plan['selected_ids']:
            folder=D/'requests'/ident;source=json.loads((folder/'source.json').read_text());body=folder/'request.json'
            assert sha(body)==source['request_sha256']
            for n in range(1,9):
                assert not (folder/f'ATTEMPT_STARTED-{n}.json').exists()
                atomic(folder/f'ATTEMPT_STARTED-{n}.json',{'attempt':n,'payload_sha256':sha(body),'unix':time.time()})
                response=folder/f'attempt-{n}.body'
                cmd=['curl','--noproxy','*','--connect-to',ROUTE,'--silent','--show-error','--retry','0','--proto','=https','--connect-timeout','30','--max-time','900','--http1.1','--header','@-','--data-binary','@'+str(body),'--output',str(response),'--write-out','%{http_code} %{ssl_verify_result} %{size_upload} %{time_total}','https://openrouter.ai/api/v1/chat/completions']
                start=time.monotonic()
                p=subprocess.run(cmd,input=('Authorization: Bearer '+key+'\nContent-Type: application/json\n').encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                (folder/f'transport-{n}.private.log').write_bytes(p.stderr.replace(key.encode(),b'[redacted]'))
                metrics=p.stdout.decode().split();status=int(metrics[0]) if metrics else 0
                record={'attempt':n,'payload_sha256':sha(body),'http_status':status,'transport_exit':p.returncode,'tls_verify':metrics[1] if len(metrics)>1 else None,'uploaded_bytes':metrics[2] if len(metrics)>2 else None,'latency_s':time.monotonic()-start,'accepted':False,'usage':None}
                j={};ans=None
                try:
                    raw=response.read_text();assert key not in raw
                    j=json.loads(raw);record['usage']=j.get('usage')
                    assert p.returncode==0 and status==200 and record['tls_verify']=='0'
                    ans=validate_body(j,source['category']);record['accepted']=True
                except Exception as e:record['error_type']=type(e).__name__
                atomic(folder/f'attempt-{n}.json',record)
                if record['accepted']:
                    atomic(folder/'ACCEPTED.json',{'id':ident,'category':source['category'],'answer':ans,'attempt':n,'body_sha256':sha(response),'request_sha256':sha(body)})
                    completed+=1;atomic(D/'status.json',{'phase':'running','accepted':completed,'unix':time.time()});break
                if p.returncode or status!=200 or j.get('model')!=MODEL or j.get('provider')!='DeepInfra':
                    raise RuntimeError('transport_or_route_failure_stop_for_review')
                if n==8:raise RuntimeError('new_payload_budget_exhausted')
                time.sleep(2)
        atomic(D/'status.json',{'phase':'answers_complete_awaiting_independent_audit','accepted':completed,'unix':time.time()})
    except Exception as e:
        (D/'error.private.log').write_text(traceback.format_exc().replace(key,'[redacted]'))
        atomic(D/'status.json',{'phase':'failed','accepted':completed,'error_type':type(e).__name__,'unix':time.time()})
        return 1
    return 0

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':sys.exit(run())
