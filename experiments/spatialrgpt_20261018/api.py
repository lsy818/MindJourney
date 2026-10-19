"""Pinned OpenRouter route; bounded identical-payload attempts and private audit."""
import base64
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from common import atomic, sha

MODEL='deepseek/deepseek-v4.1-flash'
PROVIDER='deepinfra/fp8'
ENDPOINT='https://openrouter.ai/api/v1/chat/completions'

class APIError(RuntimeError): pass

def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError('duplicate JSON key')
        d[k]=v
    return d

def schema(kind,n):
    prop=({'type':'array','items':{'type':'integer','minimum':0,'maximum':9},'minItems':n,'maxItems':n}
          if kind=='scores' else {'type':'string','pattern':'^<answer>[^<>]+</answer>$',
                                 'description':'Include the literal opening <answer> and closing </answer> tags around one numeric quantity with unit, or one clock hour.'})
    return {'type':'object','properties':{kind:prop},'required':[kind],'additionalProperties':False}

def decode(text,kind,n):
    x=json.loads(text,object_pairs_hook=unique_pairs)
    if type(x)!=dict or set(x)!={kind}: raise ValueError('invalid keys')
    v=x[kind]
    if kind=='scores':
        if type(v)!=list or len(v)!=n or any(type(i)!=int or not 0<=i<=9 for i in v): raise ValueError('invalid scores')
    else:
        if type(v)!=str or not re.fullmatch(r'<answer>[^<>]+</answer>',v.strip()): raise ValueError('invalid final envelope')
        v=v.strip()
        inner=v[len('<answer>'):-len('</answer>')].strip()
        clock=r"(?:[1-9]|1[0-2])(?:\s+o[' ]?clock)?"
        metric=r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\s*(?:millimeters?|millimetres?|mm|meters?|metres?|m|centimeters?|centimetres?|cm|inches?|inch|in|feet|foot|ft)'
        if not re.fullmatch(clock if n=='direction' else metric,inner,re.I): raise ValueError('final quantity/unit invalid')
    return v

class Client:
    def __init__(self,keyfile,audit):
        p=Path(keyfile)
        if p.stat().st_mode & 0o077: raise APIError('credential permissions')
        self.key=p.read_text().strip(); self.audit=Path(audit); self.calls=0; self.receipts=[]
        self.audit.mkdir(parents=True,exist_ok=True)

    def complete(self,system,content,kind,n):
        parts=[]; images=[]
        for item in content:
            parts.append({'type':'text','text':item[0]})
            if len(item)==2:
                p=Path(item[1]); b=p.read_bytes()
                mime='image/png' if b.startswith(b'\x89PNG') else 'image/jpeg'
                parts.append({'type':'image_url','image_url':{'url':'data:'+mime+';base64,'+base64.b64encode(b).decode(),'detail':'high'}})
                images.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest()})
        payload={'model':MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':parts}],
                 'temperature':0,'top_p':1,'max_tokens':8192,'reasoning':{'effort':'none'},'stream':False,
                 'provider':{'only':[PROVIDER],'allow_fallbacks':False,'require_parameters':True},
                 'response_format':{'type':'json_schema','json_schema':{'name':'spatial_'+kind,'strict':True,'schema':schema(kind,n)}}}
        encoded=json.dumps(payload,ensure_ascii=False).encode(); digest=hashlib.sha256(encoded).hexdigest()
        call=self.calls; self.calls+=1; folder=self.audit/f'call-{call:02d}'
        import recovery
        context={'kind':kind,'count':n,'images':images,'payload_sha256':digest}
        prior,reused,value=recovery.restore_call(folder,encoded,context,kind,n)
        self.receipts.extend(prior)
        if reused:return value
        if recovery.DRY:raise recovery.RecoveryBoundary('next network request')
        if not folder.exists():
            folder.mkdir(exist_ok=False)
            (folder/'request.json').write_bytes(encoded)
            atomic(folder/'context.json',context)
        body=folder/'request.json'
        limit=recovery.attempt_limit(digest)
        route=os.environ.get('MJ_CONNECT_TO')
        if route!='openrouter.ai:443:172.27.244.19:18447':raise APIError('verified server-only route required')
        for attempt in range(len(prior),limit):
            response_path=folder/f'attempt-{attempt+1}.body'
            started=time.monotonic()
            atomic(folder/f'ATTEMPT_STARTED-{attempt+1}.json',{'attempt':attempt+1,'payload_sha256':digest,'unix':time.time(),'pid':os.getpid()})
            cmd=['curl','--silent','--show-error','--retry','0','--proto','=https','--connect-timeout','30','--max-time','900','--http1.1',
                 '--header','@-','--data-binary','@'+str(body),'--output',str(response_path), '--write-out',json.dumps({k:'%{'+v+'}' for k,v in {'http_status':'http_code','uploaded_bytes':'size_upload','downloaded_bytes':'size_download','connect_s':'time_connect','tls_s':'time_appconnect','first_byte_s':'time_starttransfer','total_s':'time_total','upload_bytes_s':'speed_upload','tls_verify':'ssl_verify_result'}.items()}),ENDPOINT]
            cmd[1:1]=['--noproxy','*','--connect-to',route]
            p=subprocess.run(cmd,input=('Authorization: Bearer '+self.key+'\nContent-Type: application/json\n').encode(),
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={k:v for k,v in os.environ.items() if k!='LD_LIBRARY_PATH'})
            try: transport=json.loads(p.stdout.decode())
            except (ValueError,UnicodeError):transport={}
            status=int(transport.get('http_status','0'))
            atomic(folder/f'transport-{attempt+1}.json',dict(transport,exit=p.returncode,payload_bytes=len(encoded),protocol='http1.1',timeout_s=900))
            (folder/f'transport-{attempt+1}.private.log').write_bytes(p.stderr.replace(self.key.encode(),b'[redacted]'))
            record={'attempt':attempt+1,'http_status':status,'transport_exit':p.returncode,'latency_s':time.monotonic()-started,
                    'payload_sha256':digest,'accepted':False,'usage':None,'model':None,'provider':None}
            error=None; value=None
            try:
                raw=response_path.read_text()
                if self.key in raw: response_path.unlink(); raise APIError('credential reflection')
                j=json.loads(raw)
                record.update(usage=j.get('usage'),model=j.get('model'),provider=j.get('provider'),response_id=j.get('id'))
                if p.returncode or status!=200 or j.get('error'): raise ValueError('transport or API error')
                if j.get('model')!=MODEL or j.get('provider')!='DeepInfra': raise APIError('model/provider mismatch')
                choices=j.get('choices',[])
                if len(choices)!=1 or choices[0].get('finish_reason')!='stop': raise ValueError('abnormal completion')
                msg=choices[0]['message']; usage=j.get('usage') or {}
                if msg.get('reasoning') or msg.get('reasoning_details') or (usage.get('completion_tokens_details') or {}).get('reasoning_tokens',0):
                    raise APIError('reasoning must be disabled')
                if usage.get('completion_tokens',8193)>8192: raise APIError('output budget violation')
                value=decode(msg.get('content'),kind,n); record['accepted']=True
            except APIError as exc: error=exc
            except (ValueError,TypeError,KeyError,OSError) as exc: error=ValueError(type(exc).__name__)
            record['error_type']=type(error).__name__ if error else None
            atomic(folder/f'attempt-{attempt+1}.json',record); self.receipts.append(record)
            if record['accepted']: return value
            if isinstance(error,APIError) or status in (400,401,402,403) or (status and status!=200 and status not in (408,409,429) and status<500):
                raise APIError('non-retryable request failure; inspect private audit')
            if p.returncode:
                raise APIError('transport failed; preserve receipt and inspect upload metrics before continuation')
            if attempt<limit-1: time.sleep([2,5,10,30,60,120,300][min(attempt,6)])
        raise APIError('identical-payload budget exhausted; inspect private audit')
