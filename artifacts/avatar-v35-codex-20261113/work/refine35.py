"""Conservative joint relaxation of the forehead/fringe surface, preserving seam correspondence."""
from pathlib import Path
from collections import Counter
import json,numpy as np
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];a=Asset(root/'outputs/zachary_character_v34_candidate.glb')
names=['SM_Character_Face','SM_Character_Hair'];pr=[a.prim(n) for n in names];arrays=[a.arr(p['attributes']['POSITION']) for p in pr];original=[x.copy() for x in arrays]
combined=np.concatenate(original);_,ids,inverse=np.unique(np.rint(combined.astype(float)*1e6).astype('i8'),axis=0,return_index=True,return_inverse=True);points=combined[ids].astype(float)
offsets=[0,len(original[0])];triangles=[a.arr(p['indices']).reshape(-1,3).copy() for p in pr];t=np.concatenate([inverse[tri+off] for tri,off in zip(triangles,offsets)])
edge=np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]),axis=1);edge,count=np.unique(edge,axis=0,return_counts=True);boundary=np.unique(edge[count!=2]);degree=np.bincount(edge.ravel(),minlength=len(points))
def smooth(lo,hi,x):
 q=np.clip((x-lo)/(hi-lo),0,1);return q*q*(3-2*q)
weight=smooth(1.604,1.616,points[:,1])*(1-smooth(1.655,1.685,points[:,1]))*smooth(.045,.075,points[:,2])*(1-smooth(.063,.085,abs(points[:,0])))
weight[boundary]=0
for old,off in zip(original,offsets):
 extremes=np.unique(np.r_[old.argmin(0),old.argmax(0)])
 weight[inverse[off+extremes]]=0
# Preserve every point participating in the blink.
blink=np.maximum(np.linalg.norm(a.arr(pr[0]['targets'][4]['POSITION']),axis=1),np.linalg.norm(a.arr(pr[0]['targets'][5]['POSITION']),axis=1))
protected=set(inverse[:len(original[0])][blink>0])
weight[list(protected)]=0
relaxed=points.copy()
for _ in range(8):
 total=np.zeros_like(points);np.add.at(total,edge[:,0],relaxed[edge[:,1]]);np.add.at(total,edge[:,1],relaxed[edge[:,0]])
 relaxed+=.28*weight[:,None]*(total/np.maximum(degree[:,None],1)-relaxed)
delta=relaxed-points;delta*=np.minimum(1,.0009/np.maximum(np.linalg.norm(delta,axis=1),1e-12))[:,None]
def crosses(x):return np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]])
old_cross=crosses(points);old_area=np.linalg.norm(old_cross,axis=1)
for _ in range(60):
 new_cross=crosses(points+delta);new_area=np.linalg.norm(new_cross,axis=1)
 bad=(np.sum(old_cross*new_cross,axis=1)<.8*old_area*new_area)|(new_area<.65*old_area)
 if not bad.any():break
 delta[np.unique(t[bad])]*=.5
assert not bad.any()
def normals(x):
 c=crosses(x);n=np.zeros_like(points)
 for k in range(3):np.add.at(n,t[:,k],c)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);return n
normal_delta=normals(points+delta)-normals(points)
reports={}
for name,p,x,old,off in zip(names,pr,arrays,original,offsets):
 inv=inverse[off:off+len(x)];x[:]=old+delta[inv];n=a.arr(p['attributes']['NORMAL']);updated=n+normal_delta[inv];updated/=np.maximum(np.linalg.norm(updated,axis=1)[:,None],1e-12)
 # Keep inactive vertices and their normals byte-identical.
 changed=np.linalg.norm(delta[inv],axis=1)>1e-9;n[changed]=updated[changed]
 reports[name]={'moved_vertex_copies':int(sum(np.linalg.norm(x-old,axis=1)>1e-7)),'max_displacement_mm':float(np.linalg.norm(x-old,axis=1).max()*1000)}
a.save(root/'outputs/zachary_character_v35_candidate.glb')
(root/'work/refine35-changes.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
