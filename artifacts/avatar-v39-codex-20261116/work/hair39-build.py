"""Tapered surface-fitted fringe locks and bounded side/rear cleanup."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v38_candidate.glb');hp=a.prim('SM_Character_Hair');old=a.arr(hp['attributes']['POSITION']).copy();tri=a.arr(hp['indices']).reshape(-1,3).copy()
_,ids,inv=np.unique(np.rint(old.astype(float)*1e6).astype('i8'),axis=0,return_index=True,return_inverse=True);p=old[ids].astype(float);lt=inv[tri]
edges,counts=np.unique(np.sort(np.concatenate([lt[:,[0,1]],lt[:,[1,2]],lt[:,[2,0]]]),axis=1),axis=0,return_counts=True)
def smooth(lo,hi,x):
 v=np.clip((x-lo)/(hi-lo),0,1);return v*v*(3-2*v)
# Only the side/rear hair surface: retain front styling, part and every mesh boundary.
w=smooth(1.57,1.61,p[:,1])*(1-smooth(1.69,1.714,p[:,1]))*(1-smooth(.015,.065,p[:,2]))
w[np.unique(edges[counts!=2])]=0;degree=np.bincount(edges.ravel(),minlength=len(p));relaxed=p.copy()
for _ in range(6):
 total=np.zeros_like(p);np.add.at(total,edges[:,0],relaxed[edges[:,1]]);np.add.at(total,edges[:,1],relaxed[edges[:,0]])
 relaxed+=.23*w[:,None]*(total/np.maximum(degree[:,None],1)-relaxed)
delta=relaxed-p;delta*=np.minimum(1,.0016/np.maximum(np.linalg.norm(delta,axis=1),1e-12))[:,None]
def crosses(x):return np.cross(x[tri[:,1]]-x[tri[:,0]],x[tri[:,2]]-x[tri[:,0]])
oc=crosses(old);area=np.linalg.norm(oc,axis=1)
for _ in range(40):
 new=old+delta[inv];nc=crosses(new);length=np.linalg.norm(nc,axis=1)
 bad=(np.sum(oc*nc,axis=1)<.8*area*length)|(length<.65*area)
 if not bad.any():break
 delta[np.unique(lt[bad])]*=.5
assert not bad.any()
def normals(cross):
 n=np.zeros_like(p)
 for c in range(3):np.add.at(n,lt[:,c],cross)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);return n[inv]
base=a.arr(hp['attributes']['NORMAL']);updated=base+normals(nc)-normals(oc);updated/=np.maximum(np.linalg.norm(updated,axis=1)[:,None],1e-12);changed=np.linalg.norm(new-old,axis=1)>1e-8;base[changed]=updated[changed];a.arr(hp['attributes']['POSITION'])[:]=new
# Build BVHs in glTF coordinates. Include raised-brow surface for clearance.
fp=a.prim('SM_Character_Face');f=a.arr(fp['attributes']['POSITION']).copy();ft=a.arr(fp['indices']).reshape(-1,3).copy();brow=f+a.arr(fp['targets'][6]['POSITION']).copy()
hair_bvh=BVHTree.FromPolygons([Vector(x) for x in new],tri.tolist(),all_triangles=True)
face_bvh=BVHTree.FromPolygons([Vector(x) for x in f],ft.tolist(),all_triangles=True)
brow_bvh=BVHTree.FromPolygons([Vector(x) for x in brow],ft.tolist(),all_triangles=True)
def front(x,y):
 hits=[tree.ray_cast(Vector((x,y,.35)),Vector((0,0,-1))) for tree in [hair_bvh,face_bvh,brow_bvh]]
 valid=[r[0].z for r in hits if r[0] is not None];assert valid,(x,y);return max(valid)
# Artist-authored curtain paths, root/control/tip and maximum width in metres.
guides=[([-.038,1.672],[-.046,1.642],[-.057,1.627],.013),
        ([-.057,1.657],[-.064,1.638],[-.068,1.623],.011),
        ([-.006,1.676],[.001,1.650],[.015,1.637],.013),
        ([.010,1.671],[.019,1.644],[.035,1.628],.016),
        ([.028,1.665],[.041,1.638],[.051,1.625],.014),
        ([.048,1.654],[.060,1.637],[.066,1.624],.012)]
vertices=[];uvs=[];faces=[];joint_rows=[];weight_rows=[];transfer=[];transferred_normals=[]
hj=a.arr(hp['attributes']['JOINTS_0']).copy();hw=a.arr(hp['attributes']['WEIGHTS_0']).copy()
for guide_index,(rootxy,control,tip,width) in enumerate(guides):
 start=len(vertices);r=np.array(rootxy);c=np.array(control);end=np.array(tip)
 for t,profile in [(0,.72),(.32,1),(.66,.73),(.88,.34)]:
  center=(1-t)**2*r+2*(1-t)*t*c+t*t*end
  tangent=2*(1-t)*(c-r)+2*t*(end-c);side=np.array([-tangent[1],tangent[0]]);side/=np.linalg.norm(side)
  for s in [-1,0,1]:
   xy=center+side*s*width*.5*profile
   offset=(-.00045 if t==0 else .00055)+(.00015 if s==0 else 0)
   vertices.append([*xy,front(*xy)+offset]);uvs.append([(s+1)/2,t])
 tipz=front(*end)+.0006;vertices.append([*end,tipz]);uvs.append([.5,1])
 for row in range(3):
  for col in range(2):
   x=start+row*3+col;y=x+3;faces.extend([[x,y,x+1],[x+1,y,y+1]])
 faces.extend([[start+9,start+12,start+10],[start+10,start+12,start+11]])
verts=np.asarray(vertices,dtype='f4');faces=np.asarray(faces,dtype='u2')
# Ensure front-facing winding and use a real Blender mesh for smooth vertex normals.
cross=np.cross(verts[faces[:,1]]-verts[faces[:,0]],verts[faces[:,2]]-verts[faces[:,0]])
faces[cross[:,2]<0]=faces[cross[:,2]<0][:,[0,2,1]]
for v in verts:
 point,normal,index,distance=hair_bvh.find_nearest(Vector(v));corners=new[tri[index]]
 matrix=np.vstack([corners.T,np.ones(3)]);bary=np.linalg.lstsq(matrix,np.r_[point[:],1],rcond=None)[0];bary=np.maximum(bary,0);bary/=bary.sum()
 transferred_normals.append((a.arr(hp['attributes']['NORMAL'])[tri[index]]*bary[:,None]).sum(axis=0))
 weights={}
 for source,b in zip(tri[index],bary):
  for joint,weight in zip(hj[source],hw[source]):weights[int(joint)]=weights.get(int(joint),0)+float(b*weight)
 chosen=sorted(weights.items(),key=lambda x:-x[1])[:4];chosen+=[(0,0)]*(4-len(chosen));j,wgt=zip(*chosen);wgt=np.array(wgt);wgt/=wgt.sum();joint_rows.append(j);weight_rows.append(wgt);transfer.append(float(distance))
conversion=np.array([[1,0,0],[0,0,-1],[0,1,0]])
mesh=bpy.data.meshes.new('Fringe39Mesh');mesh.from_pydata((verts@conversion.T).tolist(),[],faces.tolist());mesh.update()
for poly in mesh.polygons:poly.use_smooth=True
normal=np.asarray(transferred_normals);normal/=np.linalg.norm(normal,axis=1)[:,None]
np.savez(root/'work/hair39-fringe.npz',POSITION=verts,NORMAL=normal.astype('f4'),TEXCOORD_0=np.asarray(uvs,dtype='f4'),JOINTS_0=np.asarray(joint_rows,dtype='u2'),WEIGHTS_0=np.asarray(weight_rows,dtype='f4'),indices=faces)
# Existing data is retained as the baseline for the append-only fringe export.
a.save(root/'work/hair39-shape.glb')
report={'side_rear_vertices':int(changed.sum()),'side_rear_max_displacement_mm':float(np.linalg.norm(new-old,axis=1).max()*1000),'fringe_locks':len(guides),'fringe_vertices':len(verts),'fringe_triangles':len(faces),'nearest_hair_weight_transfer_distance_mm_max':max(transfer)*1000,'guides':guides}
(root/'work/hair39-shape.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
