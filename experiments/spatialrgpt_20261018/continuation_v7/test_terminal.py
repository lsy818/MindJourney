import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from api import decode,MODEL
from terminal_invalid import classify
class Tests(unittest.TestCase):
 def base(self):
  ctx={'kind':'answer','count':'width_data','payload_sha256':'synthetic'}
  bodies=[{'model':MODEL,'provider':'DeepInfra','usage':{'completion_tokens':12},'choices':[{'finish_reason':'stop','message':{'content':'{"answer":"<answer>1 unsupported_unit</answer>"}'}}]} for _ in range(8)]
  records=[{'attempt':i+1,'payload_sha256':'synthetic','accepted':False,'transport_exit':0,'http_status':200,'error_type':'ValueError','usage':{'completion_tokens':12}} for i in range(8)]
  return records,bodies,ctx
 def test_terminal(self):self.assertTrue(classify(*self.base(),decode,MODEL))
 def test_valid_rejected(self):
  a,b,c=self.base();b[0]['choices'][0]['message']['content']='{"answer":"<answer>1 m</answer>"}'
  with self.assertRaises(AssertionError):classify(a,b,c,decode,MODEL)
 def test_incomplete_rejected(self):
  a,b,c=self.base()
  with self.assertRaises(AssertionError):classify(a[:-1],b[:-1],c,decode,MODEL)
 def test_transport_rejected(self):
  a,b,c=self.base();a[0]['transport_exit']=28
  with self.assertRaises(AssertionError):classify(a,b,c,decode,MODEL)
 def test_accepted_rejected(self):
  a,b,c=self.base();a[0]['accepted']=True
  with self.assertRaises(AssertionError):classify(a,b,c,decode,MODEL)
 def test_usage_mismatch(self):
  a,b,c=self.base();a[0]['usage']={}
  with self.assertRaises(AssertionError):classify(a,b,c,decode,MODEL)
 def test_changed_payload(self):
  a,b,c=self.base();a[0]['payload_sha256']='changed'
  with self.assertRaises(AssertionError):classify(a,b,c,decode,MODEL)
if __name__=='__main__':unittest.main()
