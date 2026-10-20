"""Independent saved-evidence audit and fixed offline scoring; no network/GPU."""
import copy, hashlib, json, math, os, re, sys, time, traceback
from collections import Counter
from pathlib import Path

R=Path('/home/datasets/shiyang/mindjourney_spatialrgpt_20261018')
D=R/'ANSWER_REPAIR_V1_20261020'
C=Path('/home/comp/24482277/mindjourney_spatialrgpt_20261018_v5')
V=Path('/home/comp/24482277/mindjourney_spatialrgpt_continuation_v7')
sys.path.insert(0,str(C));sys.path.insert(0,str(V))
import audit_v6
from audit_v6 import audit_item
_hash_cache={}
def checked_sha(path):
    p=Path(path)
    def signature():
        st=p.stat();return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    before=signature();key=str(p.resolve())
    if key in _hash_cache and _hash_cache[key][0]==before:return _hash_cache[key][1]
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    assert signature()==before
    _hash_cache[key]=(before,digest)
    return digest
audit_v6.sha=checked_sha
from common import sha, atomic, load_inputs, code_identity, COUNTS
from api import decode, MODEL
from vendor.compute_score import _parse_spatialrgpt_answer, compute_score_spatialrgpt

def main():
    os.umask(0o077)
    assert not (D/'FINAL_VERIFIED.json').exists() and not (D/'VERIFY_V3_STARTED.json').exists()
    atomic(D/'VERIFY_V3_STARTED.json',{'pid':os.getpid(),'unix':time.time(),'auditor_sha256':sha(Path(__file__))})
    atomic(D/'verify_v3_status.json',{'phase':'auditing','checked':0})
    try:
        plan=json.loads((D/'PLAN.json').read_text())
        assert plan['old_receipt_sha256']==sha(R/'FINAL_VERIFIED.json')
        assert plan['old_summary_sha256']==sha(R/'FINAL_SUMMARY.json')
        assert plan['frozen_code_identity']==code_identity()
        import recovery
        recovery.ROOT=R/'dev-v2'
        baseline_path=R/'RECOVERY_V5/BASELINE.json'
        recovery.BASELINE=json.loads(baseline_path.read_text())
        recovery.check_baseline()
        proof=json.loads((R/'RECOVERY_V5/OFFLINE_REPLAY.json').read_text())
        assert proof['passed'] and proof['code_identity']==code_identity() and proof['baseline_sha256']==sha(baseline_path)
        gate=json.loads((R/'PREFLIGHT_PASSED.json').read_text())
        assert gate['passed'] and gate['code_identity']==code_identity()
        receipt=json.loads((R/'FINAL_VERIFIED.json').read_text());selected=set(plan['selected_ids'])
        assert len(selected)==7
        rows=load_inputs(R/'shared');assert len(rows)==749
        devrows={x['id']:x for x in load_inputs(R/'shared-preflight')}
        assert set(devrows)=={x['id'] for x in rows}
        original={};answers={};attempts=[];keys=set();old_attempt_count=0;new_attempt_count=0
        source_hashes={};repair_hashes={};valid=Counter()
        for idx,row in enumerate(rows):
            ident=row['id'];root=Path(receipt['item_sources'][ident]);item=root/'items'/(ident+'.json')
            assert sha(item)==receipt['item_sha256'][ident]
            auditrow=devrows[ident] if root.name=='dev-v2' else row
            assert all(auditrow[k]==row[k] for k in ('id','category','question','raw_sha256','marked_sha256','regions_sha256','image_size'))
            x=audit_item(auditrow,root);original[ident]=x;source_hashes[ident]=sha(item)
            for call in sorted((root/ident/'api').glob('call-*')):
                for f in sorted(call.glob('attempt-*.json'),key=lambda f:int(f.stem.split('-')[-1])):
                    key=(str(f.resolve()),sha(f));assert key not in keys;keys.add(key)
                    attempts.append(json.loads(f.read_text()));old_attempt_count+=1
            if ident not in selected:
                assert x['status']=='ok';answers[ident]=x['final_answer']
            else:
                assert x['status']=='invalid_answer'
                folder=D/'requests'/ident;source=json.loads((folder/'source.json').read_text())
                call=sorted((root/ident/'api').glob('call-*'))[-1]
                assert str(call)==source['original_call'] and sha(call/'request.json')==source['original_payload_sha256']
                old=json.loads((call/'request.json').read_text());new=json.loads((folder/'request.json').read_text())
                assert new['messages'][1:]==old['messages'][1:]
                assert new['messages'][0]['content']==old['messages'][0]['content']+plan['format_instruction']
                norm=copy.deepcopy(new);norm['messages'][0]=old['messages'][0];norm['response_format']=old['response_format'];assert norm==old
                expected=copy.deepcopy(old['response_format'])
                expected['json_schema']['schema']['properties']['answer'].update(pattern=plan['pattern'],description='One finite non-negative physical length in meters inside literal answer tags, with a space before m.')
                assert new['response_format']==expected
                assert new['model']==MODEL and new['temperature']==0 and new['top_p']==1 and new['max_tokens']==8192
                assert new['reasoning']=={'effort':'none'} and new['provider']==old['provider']
                ctx=json.loads((call/'context.json').read_text());assert ctx['images']==source['images']
                files=sorted(folder.glob('attempt-*.json'),key=lambda f:int(f.stem.split('-')[-1]))
                starts=list(folder.glob('ATTEMPT_STARTED-*.json'));assert 1<=len(files)<=8 and len(starts)==len(files)
                accepted=[]
                for n,f in enumerate(files,1):
                    rec=json.loads(f.read_text());body=folder/f'attempt-{n}.body';j=json.loads(body.read_text())
                    assert rec['attempt']==n and rec['payload_sha256']==sha(folder/'request.json')==source['request_sha256']
                    assert rec['usage']==j.get('usage') and rec['http_status']==200 and rec['transport_exit']==0 and rec['tls_verify']=='0'
                    assert j['model']==MODEL and j['provider']=='DeepInfra' and not j.get('error')
                    assert len(j['choices'])==1 and j['choices'][0]['finish_reason']=='stop'
                    msg=j['choices'][0]['message'];u=j['usage']
                    assert not msg.get('reasoning') and not msg.get('reasoning_details') and not (u.get('completion_tokens_details') or {}).get('reasoning_tokens',0)
                    assert u['completion_tokens']<=8192
                    parsed=None
                    try:
                        a=decode(msg['content'],'answer',row['category'])
                        if re.fullmatch(plan['pattern'],a) and math.isfinite(_parse_spatialrgpt_answer(a,row['category'])):parsed=a
                    except (ValueError,TypeError,KeyError):pass
                    assert rec['accepted']==(parsed is not None)
                    if parsed is not None:assert n==len(files);accepted.append(parsed)
                    key=(str(f.resolve()),sha(f));assert key not in keys;keys.add(key);attempts.append(rec);new_attempt_count+=1
                assert len(accepted)==1;answers[ident]=accepted[0]
                saved=json.loads((folder/'ACCEPTED.json').read_text());assert saved['answer']==accepted[0] and saved['attempt']==len(files)
                assert saved['body_sha256']==sha(folder/f'attempt-{len(files)}.body')
                repair_hashes[ident]={'accepted_sha256':sha(folder/'ACCEPTED.json'),'request_sha256':sha(folder/'request.json'),'source_item_sha256':sha(item)}
            value=decode(json.dumps({'answer':answers[ident]}),'answer',row['category'])
            number=_parse_spatialrgpt_answer(value,row['category']);assert math.isfinite(number) and number>=0
            valid[row['category']]+=1
            if (idx+1)%100==0:atomic(D/'verify_v3_status.json',{'phase':'auditing','checked':idx+1})
        assert len(answers)==749 and dict(valid)==COUNTS and old_attempt_count==3446
        assert sha(C/'vendor/compute_score.py')=='5acac7af6f0c7459740a05e0e81ea5cee56f2df557f1d2e1891a9979961040d0'
        labelsfile=R/'shared/evaluation/labels.jsonl';assert sha(labelsfile)=='41752ec0a02365571d712f717d0e1c73f9cc8ddc3aea1dc4217d79380b335c2a'
        labels={x['id']:x for x in map(json.loads,labelsfile.read_text().splitlines())};assert set(labels)==set(answers)
        correct=Counter();oldcorrect=0;repair_correct=0
        for ident,ans in answers.items():
            gt=labels[ident];cat=original[ident]['category'];assert gt['category']==cat
            score=compute_score_spatialrgpt(ans,gt['ground_truth'],cat);correct[cat]+=score
            oldcorrect+=compute_score_spatialrgpt(original[ident]['final_answer'],gt['ground_truth'],cat)
            if ident in selected:repair_correct+=score
        assert oldcorrect==374
        costs=[x['usage']['cost'] for x in attempts if isinstance(x.get('usage'),dict) and x['usage'].get('cost') is not None]
        newcosts=[json.loads(f.read_text())['usage']['cost'] for ident in selected for f in (D/'requests'/ident).glob('attempt-*.json') if json.loads(f.read_text())['usage'].get('cost') is not None]
        summary={'passed':True,'total':749,'valid_answers':749,'invalid_answers':0,'correct':sum(correct.values()),'accuracy':sum(correct.values())/749,'categories':{c:{'correct':correct[c],'total':n,'accuracy':correct[c]/n} for c,n in COUNTS.items()},'original_correct':374,'repaired_questions':7,'repaired_correct':repair_correct,'preserved_valid_questions':742,'new_network_attempts':new_attempt_count,'historical_network_attempts':old_attempt_count,'total_network_attempts':len(attempts),'new_known_cost_usd':sum(newcosts),'cumulative_known_cost_usd':sum(costs),'unknown_cost_attempts':len(attempts)-len(costs),'new_gpu_generations':0,'protocol':'answer_only_physical_meters_format_clarification_v1'}
        atomic(D/'ANSWERS_PRIVATE.json',answers)
        atomic(D/'FINAL_SUMMARY.json',summary)
        atomic(D/'FINAL_VERIFIED.json',{'passed':True,'count':749,'old_receipt_sha256':sha(R/'FINAL_VERIFIED.json'),'old_item_sha256':source_hashes,'repair_evidence':repair_hashes,'summary_sha256':sha(D/'FINAL_SUMMARY.json'),'answers_sha256':sha(D/'ANSWERS_PRIVATE.json'),'plan_sha256':sha(D/'PLAN.json'),'auditor_sha256':sha(Path(__file__)),'frozen_code_identity':code_identity(),'all_answers_strict_and_finite':True,'all_old_sources_audited':True,'unique_network_attempts':len(keys),'no_gpu_regeneration':True})
        atomic(D/'verify_v3_status.json',{'phase':'finished','checked':749,'passed':True})
        print(json.dumps(summary))
    except Exception as e:
        (D/'verify_v3_error.private.log').write_text(traceback.format_exc())
        atomic(D/'verify_v3_status.json',{'phase':'failed','error_type':type(e).__name__})
        raise SystemExit(1)

if __name__=='__main__':main()
