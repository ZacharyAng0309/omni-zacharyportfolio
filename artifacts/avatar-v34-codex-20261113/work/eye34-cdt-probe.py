import bpy,sys,numpy as np,json
from pathlib import Path
from collections import Counter,defaultdict
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v33_candidate.glb');p=a.prim('SM_Character_Face');x=a.pos('SM_Character_Face');tri=a.arr(p['indices']).reshape(-1,3)
_,ids,w=np.unique(np.rint(x.astype(float)*1e6).astype('i8'),axis=0,return_index=True,return_inverse=True);points=x[ids];t=w[tri];centers=x[tri].mean(1)
remove=np.zeros(len(tri),dtype=bool);patches=[]
for sign in [-1,1]:
 mask=(abs(centers[:,0]-sign*.036)<.032)&(abs(centers[:,1]-1.597)<.025)&(centers[:,2]>.045)
 selected=t[mask];ec=Counter(tuple(sorted((int(a),int(b)))) for row in selected for a,b in [(row[0],row[1]),(row[1],row[2]),(row[2],row[0])]);boundary=[e for e,n in ec.items() if n==1];adj=defaultdict(list)
 for u,v in boundary:adj[u].append(v);adj[v].append(u)
 assert all(len(ns)==2 for ns in adj.values())
 remaining=set(adj);loops=[]
 while remaining:
  start=next(iter(remaining));loop=[start];previous=None;current=start
  while True:
   next_vertex=next(v for v in adj[current] if v!=previous)
   if next_vertex==start:break
   loop.append(next_vertex);previous,current=current,next_vertex
  remaining.difference_update(loop);loops.append(loop)
 used=np.unique(selected);local={int(old):i for i,old in enumerate(used)}
 verts=[Vector(points[i,:2]) for i in used]
 faces=[[local[i] for i in loop] for loop in loops]
 result=delaunay_2d_cdt(verts,[],faces,1,1e-7,True)
 vx,edges,faces_out,vo,eo,fo=result
 assert all(orig for orig in vo),'No invented coordinates in this topology repair'
 mapping=[int(used[max(orig,key=lambda i:points[used[i],2])]) for orig in vo]
 new=np.array([[mapping[i] for i in face] for face in faces_out],dtype=int)
 assert new.shape[1]==3
 cross=np.cross(points[new[:,1]]-points[new[:,0]],points[new[:,2]]-points[new[:,0]])
 new[cross[:,2]<0]=new[cross[:,2]<0][:,[0,2,1]]
 patches.append(new);remove|=mask
 print(sign,'old/new',len(selected),len(new),'loops',list(map(len,loops)))
combined=np.concatenate([t[~remove],*patches]);ec=Counter(tuple(sorted((int(a),int(b)))) for r in combined for a,b in [(r[0],r[1]),(r[1],r[2]),(r[2],r[0])]);print('edges',Counter(ec.values()))
np.savez(root/'work/eye34-retopo.npz',points=points,triangles=combined,source_ids=ids,patched=np.r_[np.zeros(sum(~remove),dtype=bool),np.ones(sum(len(v) for v in patches),dtype=bool)])
