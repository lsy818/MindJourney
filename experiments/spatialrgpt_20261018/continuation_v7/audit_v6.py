"""Read-only item audit; offline final scoring uses separate labels afterward."""
import argparse, base64, hashlib, json, os, statistics
from pathlib import Path
from collections import Counter
import sys
sys.path.insert(0,'/home/comp/24482277/mindjourney_spatialrgpt_20261018_v5')
from common import atomic, sha, load_inputs, code_identity, COUNTS
from terminal_invalid import classify
from api import decode, schema, MODEL, PROVIDER

def audit_item(row,root):
    item=json.loads((root/'items'/f'{row["id"]}.json').read_text())
    assert item['id']==row['id'] and item['category']==row['category'] and item['status'] in ('ok','invalid_answer')
    invalid=item['status']=='invalid_answer'
    trace=root/row['id']; assert Path(item['trace_path'])==trace
    if invalid:
        certpath=Path(item['terminal_receipt']);assert sha(certpath)==item['terminal_receipt_sha256']
        cert=json.loads(certpath.read_text());assert cert['passed'] and cert['id']==row['id'] and cert['attempts']==8
        assert cert['policy']=='eight_failed_final_quantity_validations_zero_score_no_new_request'
        assert sha(trace/'FAILED.json')==cert['failure_sha256']
        for name,digest in cert['files'].items():assert sha(root/name)==digest
        assert item['prediction']==item['final_answer']=='' and item['error']=='strict_final_quantity_validation_exhausted'
    else:assert not (trace/'FAILED.json').exists()
    routing=json.loads((trace/'input_routing.json').read_text())
    assert routing['raw_sha256']==row['raw_sha256'] and routing['marked_sha256']==row['marked_sha256']
    assert routing['generated_region_overlay'] is False and routing['vlm_image']==row['marked_image']
    assert Path(routing['svc_image'])==trace/'step_0/img_0.png'
    calls=sorted((trace/'api').glob('call-*'))
    assert 1<=len(calls)<=7 and item['vlm_calls']==len(calls)
    receipts=[]; kinds=[]
    for i,call in enumerate(calls):
        assert call.name==f'call-{i:02d}'
        payload=json.loads((call/'request.json').read_text());digest=sha(call/'request.json')
        ctx=json.loads((call/'context.json').read_text());assert ctx['payload_sha256']==digest
        assert payload['model']==MODEL and payload['max_tokens']==8192
        assert payload['temperature']==0 and payload['top_p']==1 and payload['reasoning']=={'effort':'none'}
        assert payload['provider']=={'only':[PROVIDER],'allow_fallbacks':False,'require_parameters':True}
        kind=ctx['kind'];kinds.append(kind)
        assert payload['response_format']=={'type':'json_schema','json_schema':{'name':'spatial_'+kind,'strict':True,'schema':schema(kind,ctx['count'])}}
        images=[p['image_url']['url'] for p in payload['messages'][1]['content'] if p['type']=='image_url']
        assert len(images)==len(ctx['images']) and images
        if kind=='scores':assert ctx['count']==len(images)-1
        assert ctx['images'][0]=={'path':row['marked_image'],'sha256':row['marked_sha256']}
        for n,(url,info) in enumerate(zip(images,ctx['images'])):
            p=Path(info['path'])
            if n:assert p.is_relative_to(trace) and p!=trace/'step_0/img_0.png'
            assert sha(p)==info['sha256']==hashlib.sha256(base64.b64decode(url.split(',',1)[1],validate=True)).hexdigest()
        attempts=sorted(call.glob('attempt-*.json'),key=lambda p:int(p.stem.split('-')[-1]))
        import recovery
        assert 1<=len(attempts)<=recovery.attempt_limit(digest)
        accepted=[]
        for n,f in enumerate(attempts,1):
            r=json.loads(f.read_text()); assert r['attempt']==n and r['payload_sha256']==digest
            body=call/f'attempt-{n}.body'
            if body.exists():
                try:j=json.loads(body.read_text())
                except (ValueError,UnicodeError):j={}
                assert r['usage']==j.get('usage')
            if r['accepted']:
                assert body.exists()
                assert n==len(attempts) and r['http_status']==200 and r['transport_exit']==0
                assert j['model']==MODEL and j['provider']=='DeepInfra'
                c=j['choices'][0];assert c['finish_reason']=='stop'
                assert not c['message'].get('reasoning') and not c['message'].get('reasoning_details')
                assert (j['usage'].get('completion_tokens_details') or {}).get('reasoning_tokens',0)==0
                assert j['usage']['completion_tokens']<=8192
                accepted.append(decode(c['message']['content'],kind,ctx['count']))
            receipts.append(r)
        if invalid and kind=='answer':
            assert i==len(calls)-1 and not accepted
            rr=[json.loads(f.read_text()) for f in attempts]
            classify(rr,[json.loads(f.with_suffix('.body').read_text()) for f in attempts],ctx,decode,MODEL)
            assert cert['payload_sha256']==digest
        else:
            assert len(accepted)==1
            if kind=='answer':assert accepted[0]==item['final_answer']==item['prediction']
    assert kinds[-1]=='answer' and all(k=='scores' for k in kinds[:-1]) and len(kinds)%2==1
    assert receipts==item['usage_attempts'] and len(receipts)==item['network_attempts']
    assert 3<=item['tool_calls']<=15
    return item

def main():
    p=argparse.ArgumentParser();p.add_argument('--shared',required=True);p.add_argument('--output',required=True)
    p.add_argument('--preflight',action='store_true');a=p.parse_args();os.umask(0o077)
    shared,root=Path(a.shared),Path(a.output); rows=load_inputs(shared)
    if a.preflight:
        ids=json.loads((shared/'development_ids.json').read_text())
        if isinstance(ids,dict):ids=ids['development_ids']
        rows=[r for r in rows if r['id'] in ids];assert len(rows)==6 and len({r['category'] for r in rows})==6
    devrows=[];devroot=root.parent/'dev-v2'
    if not a.preflight:
        gate=json.loads((root.parent/'PREFLIGHT_PASSED.json').read_text())
        assert gate['passed'] and gate['code_identity']==code_identity()
        assert gate['manifest_sha256']==sha(shared/'inputs/spatialrgpt.jsonl')
        devrows=[r for r in load_inputs(root.parent/'shared-preflight') if r['id'] in gate['item_sha256']]
        assert len(devrows)==6
        for r in devrows:assert sha(devroot/'items'/(r['id']+'.json'))==gate['item_sha256'][r['id']]
    expected={r['id'] for r in rows}-{r['id'] for r in devrows}
    assert {p.stem for p in (root/'items').glob('*.json')}==expected
    baseline_path=root.parent/'RECOVERY_V5/BASELINE.json'
    recovered=a.preflight and baseline_path.exists() and json.loads(baseline_path.read_text())['output']==str(root)
    if recovered:
        import recovery
        recovery.ROOT=root;recovery.BASELINE=json.loads(baseline_path.read_text());recovery.check_baseline()
        proof=json.loads((baseline_path.parent/'OFFLINE_REPLAY.json').read_text())
        assert proof['passed'] and proof['code_identity']==code_identity() and proof['baseline_sha256']==sha(baseline_path)
    settings=[(f,json.loads(f.read_text())) for f in root.glob('settings-*.json')]
    assert settings and any(s['code_identity']==code_identity() for _,s in settings)
    for f,s in settings:
        if s['code_identity']==code_identity():continue
        assert recovered and s['code_identity'] in recovery.BASELINE['prior_code_identities']
        assert sha(f)==recovery.BASELINE['files'][str(f.relative_to(root))]
        current=next(v for _,v in settings if v['code_identity']==code_identity())
        assert s['arguments']==current['arguments'] and s['mode']==current['mode']
    if not a.preflight:
        import recovery
        recovery.ROOT=devroot;recovery.BASELINE=json.loads(baseline_path.read_text());recovery.check_baseline()
        proof=json.loads((baseline_path.parent/'OFFLINE_REPLAY.json').read_text())
        assert proof['passed'] and proof['code_identity']==code_identity() and proof['baseline_sha256']==sha(baseline_path)
    items=[audit_item(r,root) for r in rows if r['id'] in expected]+[audit_item(r,devroot) for r in devrows]
    assert len(items)==len({x['id'] for x in items})==len(rows)
    sources={x['id']:(root if x['id'] in expected else devroot) for x in items}
    receipt={'passed':True,'count':len(items),'code_identity':code_identity(),'manifest_sha256':sha(shared/'inputs/spatialrgpt.jsonl'),
             'item_sha256':{x['id']:sha(sources[x['id']]/'items'/f'{x["id"]}.json') for x in items},'item_sources':{k:str(v) for k,v in sources.items()}}
    if a.preflight:
        if recovered:receipt.update(recovery_baseline_sha256=sha(baseline_path),offline_replay_sha256=sha(baseline_path.parent/'OFFLINE_REPLAY.json'))
        atomic(root.parent/'PREFLIGHT_PASSED.json',receipt)
        print(json.dumps({'preflight_passed':True,'count':len(items)}));return
    assert len(items)==749
    from vendor.compute_score import compute_score_spatialrgpt
    assert sha(Path('/home/comp/24482277/mindjourney_spatialrgpt_20261018_v5/vendor/compute_score.py'))=='5acac7af6f0c7459740a05e0e81ea5cee56f2df557f1d2e1891a9979961040d0'
    labels=[json.loads(x) for x in (shared/'evaluation/labels.jsonl').read_text().splitlines()]
    assert sha(shared/'evaluation/labels.jsonl')=='41752ec0a02365571d712f717d0e1c73f9cc8ddc3aea1dc4217d79380b335c2a'
    assert len(labels)==749 and len({x['id'] for x in labels})==749
    labels={x['id']:x for x in labels};assert set(labels)=={r['id'] for r in rows}
    correct=Counter(); attempts=[]
    for x in items:
        gt=labels[x['id']];assert gt['category']==x['category']
        correct[x['category']]+=compute_score_spatialrgpt(x['final_answer'],gt['ground_truth'],x['category'])
        attempts.extend(x['usage_attempts'])
    costs=[r['usage'].get('cost') for r in attempts if isinstance(r.get('usage'),dict) and r['usage'].get('cost') is not None]
    summary={'passed':True,'total':749,'correct':sum(correct.values()),'accuracy':sum(correct.values())/749,
             'categories':{c:{'correct':correct[c],'total':n,'accuracy':correct[c]/n} for c,n in COUNTS.items()},
             'statuses':dict(Counter(x['status'] for x in items)),'mean_latency_s':statistics.mean(x['latency_s'] for x in items),
             'vlm_calls':sum(x['vlm_calls'] for x in items),'tool_calls':sum(x['tool_calls'] for x in items),
             'network_attempts':len(attempts),'known_cost_usd':sum(costs),'unknown_cost_attempts':len(attempts)-len(costs),
             'labels_sha256':sha(shared/'evaluation/labels.jsonl')}
    receipt['continuation_auditor_sha256']=sha(Path(__file__))
    receipt['terminal_validator_sha256']=sha(Path(__file__).with_name('terminal_invalid.py'))
    receipt['invalid_answer_count']=sum(x['status']=='invalid_answer' for x in items)
    assert not (root.parent/'FINAL_SUMMARY.json').exists() and not (root.parent/'FINAL_VERIFIED.json').exists()
    atomic(root.parent/'FINAL_SUMMARY.json',summary);atomic(root.parent/'FINAL_VERIFIED.json',receipt)
    print(json.dumps(summary))

if __name__=='__main__':main()
