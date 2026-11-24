from pathlib import Path
import numpy as np,json
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];a=Asset(root/'outputs/zachary_character_v39_candidate.glb');names=['SM_Character_Face','SM_Character_Hair'];pr=[a.prim(n) for n in names];original=[a.pos(n).copy() for n in names];offsets=np.cumsum([0]+[len(x) for x in original]);combined=np.concatenate(original)
_,ids,inv=np.unique(np.rint(combined.astype(float)*1e6).astype('i8'),axis=0,return_index=True,return_inverse=True);p=combined[ids].astype(float);tri=np.concatenate([a.arr(q['indices']).reshape(-1,3)+offsets[i] for i,q in enumerate(pr)]);t=inv[tri]
edges,count=np.unique(np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]),axis=1),axis=0,return_counts=True)
def smooth(lo,hi,x):
 q=np.clip((x-lo)/(hi-lo),0,1);return q*q*(3-2*q)
radius=np.sqrt(((p[:,0]+.017)/.024)**2+((p[:,1]-1.653)/.025)**2);w=(1-smooth(.15,1,radius))*smooth(.055,.085,p[:,2]);w[np.unique(edges[count!=2])]=0
for target in pr[0]['targets']:
 moving=np.linalg.norm(a.arr(target['POSITION']),axis=1)>1e-7;w[inv[:len(original[0])][moving]]=0
degree=np.bincount(edges.ravel(),minlength=len(p));relaxed=p.copy()
for _ in range(12):
 total=np.zeros_like(p);np.add.at(total,edges[:,0],relaxed[edges[:,1]]);np.add.at(total,edges[:,1],relaxed[edges[:,0]]);relaxed+=.35*w[:,None]*(total/np.maximum(degree[:,None],1)-relaxed)
d=relaxed-p;d*=np.minimum(1,.002/np.maximum(np.linalg.norm(d,axis=1),1e-12))[:,None]
def cross(x):return np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]])
oc=cross(p);oa=np.linalg.norm(oc,axis=1)
for _ in range(50):
 nc=cross(p+d);na=np.linalg.norm(nc,axis=1);bad=(np.sum(oc*nc,axis=1)<.8*oa*na)|(na<.65*oa)
 if not bad.any():break
 d[np.unique(t[bad])]*=.5
assert not bad.any()
def normal(c):
 n=np.zeros_like(p)
 for k in range(3):np.add.at(n,t[:,k],c)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);return n
nd=normal(nc)-normal(oc);report={}
for i,(name,q,old) in enumerate(zip(names,pr,original)):
 mapping=inv[offsets[i]:offsets[i+1]];new=(old+d[mapping]).astype('f4');active=np.linalg.norm(new-old,axis=1)>1e-8;a.arr(q['attributes']['POSITION'])[:]=new;n=a.arr(q['attributes']['NORMAL']);updated=n+nd[mapping];updated/=np.maximum(np.linalg.norm(updated,axis=1)[:,None],1e-12);n[active]=updated[active];report[name]={'vertices':int(active.sum()),'max_mm':float(np.linalg.norm(new-old,axis=1).max()*1000)}
a.save(root/'work/fringe40-shape.glb');(root/'work/fringe40-shape.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
