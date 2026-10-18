"""Three synthetic, non-benchmark capability checks with private receipts."""
from pathlib import Path
import json, os, sys
from PIL import Image
from api import Client, MODEL, PROVIDER
from common import atomic

def main():
    os.umask(0o077)
    root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=False)
    im=Image.new('RGB',(256,256),'red');im.paste('blue',(128,0,256,256));im.save(root/'synthetic.png')
    client=Client(sys.argv[2],root/'audit')
    system='Follow the requested JSON schema exactly. Use the image when requested.'
    score=client.complete(system,[('For the left and right halves respectively: give score 1 for red, 2 for blue. Return the two scores in order.',str(root/'synthetic.png'))],'scores',2)
    assert score==[1,2]
    metric=client.complete(system,[('Return exactly {"answer":"<answer>1 m</answer>"}.',)],'answer','width_data')
    clock=client.complete(system,[("Return an answer with exactly 12 o'clock inside the answer tags, in the JSON answer property.",)],'answer','direction')
    assert metric=='<answer>1 m</answer>' and "12" in clock
    receipt={'passed':True,'model':MODEL,'provider':PROVIDER,'calls':client.calls,'attempts':client.receipts}
    atomic(root/'COMPLETE.json',receipt)
    print(json.dumps({'passed':True,'model':MODEL,'provider':PROVIDER,'calls':client.calls,'network_attempts':len(client.receipts)}))

if __name__=='__main__':main()
