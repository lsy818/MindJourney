"""Offline verification only: all Parquet records and common package alignment."""
import ast
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import sys
import numpy as np
import pyarrow.parquet as pq
from PIL import Image

def decode_rle(rle):
    h,w=rle['size']; counts=rle['counts']
    if isinstance(counts,(str,bytes)):
        s=counts.decode() if isinstance(counts,bytes) else counts
        counts=[];p=0
        while p<len(s):
            x=0;k=0
            while True:
                c=ord(s[p])-48;p+=1;x|=(c&31)<<(5*k);k+=1
                if not c&32:
                    if c&16:x|=-1<<(5*k)
                    break
            if len(counts)>2:x+=counts[-2]
            counts.append(x)
    assert all(type(x)==int and x>=0 for x in counts) and sum(counts)==h*w
    flat=np.empty(h*w,dtype=bool);pos=0
    for i,n in enumerate(counts):flat[pos:pos+n]=bool(i%2);pos+=n
    return flat.reshape((h,w),order='F')

def parse(v):
    if not isinstance(v,str): return v
    try: return json.loads(v)
    except ValueError:return ast.literal_eval(v)

def main():
    source,shared=map(Path,sys.argv[1:3])
    rows=[json.loads(x) for x in (shared/'inputs/spatialrgpt.jsonl').read_text().splitlines()]
    lookup={r['id']:r for r in rows}; seen=set();counts=Counter();total=0
    for name in ['0000.parquet','0001.parquet','0002.parquet']:
        for r in pq.read_table(source/name).to_pylist():
            total+=1;qa=parse(r['qa_info']);boxes=np.asarray(parse(r['bbox']),dtype=float)
            im=Image.open(io.BytesIO(r['image']['bytes'])).convert('RGB');im.load()
            rles=parse(r['rle']); masks=[]
            for rl in rles:
                m=decode_rle(rl);assert m.shape==(im.height,im.width);masks.append(m)
            assert boxes.shape==(len(masks),4)
            assert all(0<=x1<=x2<=im.width and 0<=y1<=y2<=im.height for x1,y1,x2,y2 in boxes)
            if qa['type']!='quantitative':continue
            qid=r['id'];assert qid not in seen;seen.add(qid);row=lookup[qid]
            suffix='\n\nThe region labels identify the target objects in the original image.\nAnswer the original question using the original image as the reference view.\nReturn one final answer inside <answer>...</answer>.\nFor a distance or size, give one non-negative number and an explicit unit.\nFor a direction, give one integer clock hour from 1 to 12.'
            assert row['category']==qa['category'] and row['question']==r['text_q']+suffix
            assert np.array_equal(np.asarray(im),np.asarray(Image.open(row['raw_image']).convert('RGB')))
            with np.load(row['regions_path'],allow_pickle=False) as z:
                assert np.array_equal(z['bbox'],boxes) and np.array_equal(z['masks'],np.asarray(masks))
            counts[qa['category']]+=1
    assert total==1406 and len(seen)==749 and seen==set(lookup)
    print(json.dumps({'passed':True,'source_decoded':total,'quantitative':len(seen),'counts':dict(counts),
                     'raw_pixels_questions_regions_ids':'exactly_aligned','generated_or_geometry_cache_used':False}))

if __name__=='__main__':main()
