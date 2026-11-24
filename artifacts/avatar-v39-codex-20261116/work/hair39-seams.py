"""Resolve UV-split shading on the face/lids, preserving all pose positions."""
from pathlib import Path
import numpy as np,json
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];a=Asset(root/'work/hair39-shape.glb')
names=['SM_Character_Face','SM_Character_Eyelids'];primitives=[a.prim(n) for n in names]
positions=[a.arr(p['attributes']['POSITION']).copy() for p in primitives];normals=[a.arr(p['attributes']['NORMAL']).copy() for p in primitives];counts=list(map(len,positions));offsets=np.cumsum([0]+counts)
points=np.concatenate(positions).astype(float);old=np.concatenate(normals).astype(float)
_,inv=np.unique(np.rint(points*1e6).astype('i8'),axis=0,return_inverse=True)
pose_positions=[np.concatenate([a.arr(p['targets'][k]['POSITION']).copy() for p in primitives]).astype(float) for k in range(8)]
pose_normals=[np.concatenate([a.arr(p['targets'][k]['NORMAL']).copy() if 'NORMAL' in p['targets'][k] else np.zeros_like(positions[i]) for i,p in enumerate(primitives)]).astype(float)+old for k in range(8)]
base=old.copy();posed=[x.copy() for x in pose_normals];groups=[]
for key in np.unique(inv):
 ids=np.flatnonzero(inv==key)
 if len(ids)<2:continue
 if any(np.ptp(delta[ids],axis=0).max()>1e-6 for delta in pose_positions):continue
 if np.ptp(old[ids],axis=0).max()<1e-6 and all(np.ptp(n[ids],axis=0).max()<1e-6 for n in pose_normals):continue
 mean=old[ids].sum(axis=0);mean/=np.linalg.norm(mean);base[ids]=mean
 for k in range(8):
  mean=pose_normals[k][ids].sum(axis=0);mean/=np.linalg.norm(mean);posed[k][ids]=mean
 groups.append(ids.tolist())
changed=np.linalg.norm(base-old,axis=1)>1e-7
for i,p in enumerate(primitives):
 sl=slice(offsets[i],offsets[i+1]);active=changed[sl];a.arr(p['attributes']['NORMAL'])[active]=base[sl][active]
 for k,target in enumerate(p['targets']):
  delta=(posed[k]-base)[sl]
  if 'NORMAL' not in target:
   assert np.max(abs(delta))<1e-6;continue
  original=a.arr(target['NORMAL']);mask=np.linalg.norm(delta-original,axis=1)>1e-7;original[mask]=delta[mask]
  acc=a.g['accessors'][target['NORMAL']];acc.update(min=original.min(axis=0).tolist(),max=original.max(axis=0).tolist())
path=root/'outputs/zachary_character_v39_candidate.glb';a.save(path)
report={'welded_groups':len(groups),'changed_base_normal_copies':int(changed.sum()),'by_mesh':{name:int(changed[offsets[i]:offsets[i+1]].sum()) for i,name in enumerate(names)},'groups':groups,'position_tolerance_m':1e-6,'fringe_trial_included':False,'file_bytes':path.stat().st_size}
(root/'work/hair39-seams.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='groups'}))
