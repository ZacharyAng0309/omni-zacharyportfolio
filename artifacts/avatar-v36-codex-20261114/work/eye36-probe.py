import bpy,sys,json,numpy as np
from pathlib import Path
from collections import Counter,defaultdict
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v35_candidate.glb');p=a.prim('SM_Character_Face');x=a.pos('SM_Character_Face').copy();t=a.arr(p['indices']).reshape(-1,3).copy()
_,ids,w=np.unique(np.rint(x.astype(float)*1e6).astype('i8'),axis=0,return_index=True,return_inverse=True);geo=x[ids];gt=w[t];centers=x[t].mean(1)
reports=[]
for sign in [-1,1]:
 center=np.array([sign*.034,1.598]);radius=np.linalg.norm((centers[:,:2]-center)/[.014,.005],axis=1)
 mask=(radius<1.65)&(centers[:,2]>.045)
 ec=Counter(tuple(sorted((int(i),int(j)))) for row in gt[mask] for i,j in [(row[0],row[1]),(row[1],row[2]),(row[2],row[0])]);edges=[e for e,n in ec.items() if n==1];adj=defaultdict(list)
 for i,j in edges:adj[i].append(j);adj[j].append(i)
 assert all(len(ns)==2 for ns in adj.values()),dict(Counter(map(len,adj.values())))
 remaining=set(adj);loops=[]
 while remaining:
  current=min(remaining);start=current;last=None;loop=[]
  while True:
   loop.append(current);nxt=next(i for i in adj[current] if i!=last)
   if nxt==start:break
   last,current=current,nxt
  remaining.difference_update(loop);loops.append(loop)
 loop=max(loops,key=len);q=geo[loop,:2]-center;angles=np.arctan2(q[:,1]/.005,q[:,0]/.014);steps=(np.roll(angles,-1)-angles+np.pi)%(2*np.pi)-np.pi
 reports.append({'sign':sign,'removed_triangles':int(mask.sum()),'loops':list(map(len,loops)),'boundary_z':geo[loop,2].tolist(),'angles_monotonic':bool(np.all(steps>0) or np.all(steps<0)),'angle_step_range':list(map(float,[steps.min(),steps.max()])),'bounds':geo[loop].min(0).tolist()+geo[loop].max(0).tolist()})
 np.savez(root/f'work/eye36-patch{sign}.npz',mask=mask,loop=np.array(loop),points=geo,source_ids=ids)
print(json.dumps(reports));(root/'work/eye36-probe.json').write_text(json.dumps(reports,indent=2))
