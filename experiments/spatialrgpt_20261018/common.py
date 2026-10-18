"""Shared input validation. Ground truth is deliberately absent from this module."""
import hashlib
import json
from collections import Counter
from pathlib import Path

COUNTS = dict(direction=107, distance_data=148, horizontal_distance_data=122,
              vertical_distance_data=106, width_data=133, height_data=133)
SOURCE = Path('/data/zhida/saves/pySpatial/spatialrgpt-adapter-20261018')
FIELDS = {'id','category','question','raw_image','marked_image','regions_path',
          'cache_path','raw_sha256','marked_sha256','regions_sha256','image_size'}

def code_identity():
    root=Path(__file__).resolve().parent
    paths=['api.py','worker.py','search.py','common.py','audit.py','environment.sh','stage_environment.sh','FROZEN_SOURCE_SHA256.json','recovery.py']
    return {p:sha(root/p) for p in paths}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def atomic(p, value):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n'); t.replace(p)

def load_inputs(shared, validate=False, selected_ids=None):
    shared=Path(shared)
    manifest=shared/'inputs/spatialrgpt.jsonl'
    report=json.loads((shared/'validation.json').read_text())
    assert sha(manifest)==report['manifest_sha256']
    rows=[json.loads(x) for x in manifest.read_text().splitlines() if x.strip()]
    assert len(rows)==len({r['id'] for r in rows})==749
    assert Counter(r['category'] for r in rows)==COUNTS
    if validate:
        import numpy as np
        from PIL import Image
    for r in rows:
        assert set(r)==FIELDS
        assert isinstance(r['id'],str) and Path(r['id']).name==r['id']
        # Drop the other method's cache reference before handing anything to inference.
        r.pop('cache_path')
        check=validate and (selected_ids is None or r['id'] in selected_ids)
        for key,digest in [('raw_image','raw_sha256'),('marked_image','marked_sha256'),('regions_path','regions_sha256')]:
            rel=Path(r[key]).relative_to(SOURCE); assert '..' not in rel.parts
            r[key]=str(shared/rel)
            if check: assert sha(r[key])==r[digest], (r['id'],key)
        if check:
            with Image.open(r['raw_image']) as im: size=im.size; im.convert('RGB').load()
            with Image.open(r['marked_image']) as im: assert im.size==size; im.convert('RGB').load()
            assert list(size)==r['image_size']
            with np.load(r['regions_path'],allow_pickle=False) as z:
                b,m=z['bbox'],z['masks']
                assert b.ndim==2 and b.shape[1]==4 and np.isfinite(b).all()
                assert m.shape==(len(b),size[1],size[0]) and m.dtype==np.bool_
                assert all(0<=x1<=x2<=size[0] and 0<=y1<=y2<=size[1] for x1,y1,x2,y2 in b)
    return rows

if __name__=='__main__':
    import sys
    root=Path(sys.argv[1]);ids=None
    if '--preflight' in sys.argv:
        ids=json.loads((root/'development_ids.json').read_text())
        if isinstance(ids,dict):ids=ids['development_ids']
        assert len(ids)==len(set(ids))==6
    rows=load_inputs(root,True,ids)
    if ids is not None:
        selected=[r for r in rows if r['id'] in ids];assert len(selected)==6 and len({r['category'] for r in selected})==6
    receipt={'passed':True,'count':len(rows) if ids is None else len(ids),'scope':'full' if ids is None else 'preflight',
             'counts':COUNTS,'manifest_sha256':sha(root/'inputs/spatialrgpt.jsonl')}
    atomic(root.parent/('INPUTS_VERIFIED.json' if ids is None else 'INPUTS_PREFLIGHT_VERIFIED.json'),receipt); print(json.dumps(receipt))
