import hashlib,json,tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
import recovery,api
from common import atomic,sha

class Resume(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,{"MJ_CONNECT_TO":"openrouter.ai:443:172.27.244.19:18447"});self.env.start()
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.folder=self.root/'api/call-00';self.folder.mkdir(parents=True)
  self.key=self.root/'key';self.key.write_text('synthetic-test-only');self.key.chmod(0o600)
  self.encoded=b'original';self.ctx={'payload_sha256':hashlib.sha256(self.encoded).hexdigest()}
  (self.folder/'request.json').write_bytes(self.encoded);atomic(self.folder/'context.json',self.ctx)
  recovery.ROOT=self.root;recovery.DRY=False;recovery.BASELINE={'files':{'api/call-00/request.json':sha(self.folder/'request.json')},'reserved_attempts':{},'prior_job':'test'}
 def tearDown(self):
  self.env.stop()
  recovery.BASELINE=None;recovery.ROOT=None;recovery.DRY=False;self.tmp.cleanup()
 def failed(self,n):
  for i in range(1,n+1):atomic(self.folder/f'attempt-{i}.json',{'attempt':i,'payload_sha256':self.ctx['payload_sha256'],'accepted':False,'http_status':0,'transport_exit':28,'usage':None})
 def test_payload_and_context_tampering_rejected(self):
  for encoded,ctx in [(b'changed',self.ctx),(self.encoded,{'payload_sha256':'changed'})]:
   with self.assertRaises(AssertionError):recovery.restore_call(self.folder,encoded,ctx,'scores',1)
 def test_interrupted_attempt_counted_and_not_reissued(self):
  self.failed(5);recovery.BASELINE['reserved_attempts']['api/call-00']=6
  records,reused,_=recovery.restore_call(self.folder,self.encoded,self.ctx,'scores',1)
  self.assertEqual(len(records),6);self.assertFalse(reused);self.assertIsNone(records[-1]['usage'])
  self.assertEqual(list(range(len(records),8)),[6,7])
 def test_unreviewed_response_body_blocks(self):
  self.failed(5);recovery.BASELINE['reserved_attempts']['api/call-00']=6
  (self.folder/'attempt-6.body').write_text('{}')
  with self.assertRaises(AssertionError):recovery.restore_call(self.folder,self.encoded,self.ctx,'scores',1)
 def test_accepted_response_reused_without_network(self):
  j={'model':api.MODEL,'provider':'DeepInfra','usage':{'completion_tokens':3},'choices':[{'finish_reason':'stop','message':{'content':'{"scores":[8]}'}}]}
  atomic(self.folder/'attempt-1.body',j)
  atomic(self.folder/'attempt-1.json',{'attempt':1,'payload_sha256':self.ctx['payload_sha256'],'accepted':True,'http_status':200,'transport_exit':0,'usage':j['usage']})
  with patch('subprocess.run',side_effect=AssertionError('network forbidden')):
   records,reused,value=recovery.restore_call(self.folder,self.encoded,self.ctx,'scores',1)
  self.assertTrue(reused);self.assertEqual(value,[8]);self.assertEqual(len(records),1)
 def test_remaining_budget_exactly_two_requests(self):
  # Exercise the actual client loop; inherited six attempts leave only numbers7/8.
  self.folder.rename(self.root/'old');client=api.Client(self.key,self.root/'api')
  prior=[{'attempt':i} for i in range(1,7)];calls=[]
  def fake_run(cmd,**kwargs):
   calls.append(cmd);Path(cmd[cmd.index('--output')+1]).write_text('{}');return type('Result',(),{'returncode':0,'stdout':b'{"http_status":"503"}','stderr':b''})()
  with patch('recovery.restore_call',return_value=(prior,False,None)),patch('api.subprocess.run',side_effect=fake_run),patch('api.time.sleep'):
   with self.assertRaises(api.APIError):client.complete('test',[('text',)],'scores',1)
  self.assertEqual(len(calls),2)
  self.assertEqual(sorted(p.name for p in (self.root/'api/call-00').glob('attempt-*.json')),['attempt-7.json','attempt-8.json'])
  self.assertEqual(calls[0][calls[0].index('--data-binary')+1],calls[1][calls[1].index('--data-binary')+1])
 def test_exhausted_request_requires_exact_scoped_authorization(self):
  d=recovery.EXHAUSTED_DIGEST
  with self.assertRaises(AssertionError):recovery.attempt_limit(d)
  recovery.BASELINE['continuation_policy']={'payload_sha256':d,'prior_attempts':8,'additional_attempts':1,'total_limit':9,'authorization':'human_20261019_repair_then_resume'}
  self.assertEqual(recovery.attempt_limit(d),9)
  self.assertEqual(recovery.attempt_limit('different-payload'),8)
  recovery.BASELINE['continuation_policy']['total_limit']=16
  with self.assertRaises(AssertionError):recovery.attempt_limit(d)
 def test_transport_failure_is_recorded_and_not_blindly_retried(self):
  self.folder.rename(self.root/'old');client=api.Client(self.key,self.root/'api')
  result=type('Result',(),{'returncode':28,'stdout':b'{"http_status":"000","uploaded_bytes":"123"}','stderr':b'timeout'})()
  with patch('api.subprocess.run',return_value=result) as run,patch('api.time.sleep'):
   with self.assertRaises(api.APIError):client.complete('test',[('text',)],'scores',1)
  self.assertEqual(run.call_count,1)
  folder=self.root/'api/call-00'
  self.assertEqual(json.loads((folder/'transport-1.json').read_text())['uploaded_bytes'],'123')
  self.assertEqual(json.loads((folder/'attempt-1.json').read_text())['transport_exit'],28)
if __name__=='__main__':unittest.main()
