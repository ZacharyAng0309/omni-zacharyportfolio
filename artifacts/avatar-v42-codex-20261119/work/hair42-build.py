"""Bounded crown relaxation and sparse round, tapered hair filaments in Blender."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v41_candidate.glb');hp=a.prim('SM_Character_Hair')
old=a.pos('SM_Character_Hair').copy();tri=a.arr(hp['indices']).reshape(-1,3).copy()
_,ids,inv=np.unique(np.rint(old.astype(float)*1e6).astype('i8'),axis=0,return_index=True,return_inverse=True)
p=old[ids].astype(float);lt=inv[tri]
edges,counts=np.unique(np.sort(np.concatenate([lt[:,[0,1]],lt[:,[1,2]],lt[:,[2,0]]]),axis=1),axis=0,return_counts=True)
def smooth(lo,hi,x):
 t=np.clip((x-lo)/(hi-lo),0,1);return t*t*(3-2*t)
facekeys=set(map(tuple,np.rint(a.pos('SM_Character_Face').astype(float)*1e6).astype('i8')))
shared=np.array([tuple(x) in facekeys for x in np.rint(p*1e6).astype('i8')]);boundary=np.unique(edges[counts!=2])
w=smooth(1.685,1.716,p[:,1]);w[shared]=0;w[boundary]=0
degree=np.bincount(edges.ravel(),minlength=len(p));relaxed=p.copy()
for _ in range(8):
 total=np.zeros_like(p);np.add.at(total,edges[:,0],relaxed[edges[:,1]]);np.add.at(total,edges[:,1],relaxed[edges[:,0]])
 relaxed+=.24*w[:,None]*(total/np.maximum(degree[:,None],1)-relaxed)
delta=relaxed-p;delta*=np.minimum(1,.0018/np.maximum(np.linalg.norm(delta,axis=1),1e-12))[:,None]
def crosses(x):return np.cross(x[tri[:,1]]-x[tri[:,0]],x[tri[:,2]]-x[tri[:,0]])
oc=crosses(old);area=np.linalg.norm(oc,axis=1)
for _ in range(40):
 new=old+delta[inv];nc=crosses(new);length=np.linalg.norm(nc,axis=1)
 bad=(np.sum(oc*nc,axis=1)<.85*area*length)|(length<.72*area)
 if not bad.any():break
 delta[np.unique(lt[bad])]*=.5
assert not bad.any()
def normals(cross):
 n=np.zeros_like(p)
 for c in range(3):np.add.at(n,lt[:,c],cross)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);return n[inv]
base=a.arr(hp['attributes']['NORMAL']);updated=base+normals(nc)-normals(oc);updated/=np.maximum(np.linalg.norm(updated,axis=1)[:,None],1e-12)
changed=np.linalg.norm(new-old,axis=1)>1e-8;base[changed]=updated[changed];a.arr(hp['attributes']['POSITION'])[:]=new
a.save(root/'work/hair42-shape.glb')
hair_bvh=BVHTree.FromPolygons([Vector(x) for x in new],tri.tolist(),all_triangles=True)
fp=a.prim('SM_Character_Face');f=a.pos('SM_Character_Face').copy();ft=a.arr(fp['indices']).reshape(-1,3).copy()
fm=next(m for m in a.g['meshes'] if m['name']=='SM_Character_Face');browindex=fm['extras']['targetNames'].index('browInnerUp')
brow=f+a.arr(fp['targets'][browindex]['POSITION']).copy()
face_bvh=BVHTree.FromPolygons([Vector(x) for x in f],ft.tolist(),all_triangles=True)
brow_bvh=BVHTree.FromPolygons([Vector(x) for x in brow],ft.tolist(),all_triangles=True)
def front(x,y):
 hits=[tree.ray_cast(Vector((x,y,.4)),Vector((0,0,-1))) for tree in [hair_bvh,face_bvh,brow_bvh]]
 values=[r[0].z for r in hits if r[0] is not None];assert values,(x,y);return max(values)
def top(x,z):
 hit=hair_bvh.ray_cast(Vector((x,1.9,z)),Vector((0,-1,0)))[0];assert hit is not None,(x,z);return hit.y
guides=json.loads((root/'work/fringe40-guides.json').read_text())['guides_x_y_m']
rng=np.random.default_rng(42);paths=[]
# Fine individual fibers follow the part's existing outward/downward comb direction.
for i,x in enumerate(np.linspace(-.071,.073,28)):
 x+=float(rng.uniform(-.0012,.0012));line=float(np.interp(x,[v[0] for v in guides],[v[1] for v in guides]))
 sign=-1 if x<-.023 else 1
 end=np.array([x,line-float(rng.uniform(.001,.0025))]);start=end+[-sign*float(rng.uniform(.002,.005)),float(rng.uniform(.009,.015))]
 control=(start+end)/2+[-sign*.0015,.001]
 centers=[]
 for t in np.linspace(0,1,8):
  xy=(1-t)**2*start+2*t*(1-t)*control+t*t*end
  # Root below the cap, body close to the surface, distal tip above the forehead.
  offset=-.00060*(1-smooth(0,.40,t))+.00020*smooth(0,.40,t)+.00012*math.sin(math.pi*t)
  centers.append([xy[0],xy[1],front(*xy)+offset])
 paths.append({'kind':'fringe','centers':centers,'radius':float(rng.uniform(.000065,.000105))})
# Crown flyaways: short surface-conforming arcs, kept sparse and close to the cap.
for i,(x,z,dx,dz) in enumerate([(-.023,.020,-.019,.013),(-.010,.022,.021,.014),(-.004,.008,.031,.003),(.010,.011,.030,.007),(.034,.025,.022,.006),(-.039,.026,-.020,.008),(-.055,.003,-.021,.014),(.052,.010,.017,.006),(-.016,-.015,-.022,.010),(.014,-.019,.026,.008)]):
 centers=[]
 for t in np.linspace(0,1,9):
  xx=x+dx*t;zz=z+dz*t
  offset=-.00045*(1-smooth(0,.20,t))+(.0024+(.0008 if i%3==0 else 0))*math.sin(math.pi*t)**1.2+.00018*t
  centers.append([xx,top(xx,zz)+offset,zz])
 paths.append({'kind':'crown','centers':centers,'radius':float(rng.uniform(.000065,.00010))})
# Closed four-sided tubes, smooth shading, nonzero tapered tips; no alpha sorting.
vertices=[];triangles=[];colors=[];strand_ranges=[]
for index,path in enumerate(paths):
 start=len(vertices);centers=np.asarray(path['centers']);steps=len(centers);sides=4
 for row,center in enumerate(centers):
  t=row/(steps-1);tangent=centers[min(row+1,steps-1)]-centers[max(0,row-1)];tangent/=np.linalg.norm(tangent)
  reference=np.array([0,0,1]) if path['kind']=='crown' else np.array([1,0,0])
  u=np.cross(tangent,reference);u/=np.linalg.norm(u);v=np.cross(tangent,u)
  radius=path['radius']*(.18+.82*smooth(0,.12,t))*(1-.93*smooth(.58,1,t))
  for side in range(sides):
   theta=2*math.pi*side/sides;vertices.append(center+radius*(math.cos(theta)*u+math.sin(theta)*v))
   value=.90+.20*(index%5)/4;colors.append([.035*value,.022*value,.014*value,1])
 for row in range(steps-1):
  for side in range(sides):
   a0=start+row*sides+side;b=start+row*sides+(side+1)%sides;c=a0+sides;d=b+sides
   triangles.extend([[a0,b,c],[b,d,c]])
 # The ring order is counterclockwise along the local tangent.
 for side in range(1,sides-1):
  triangles.append([start,start+side+1,start+side]);end=start+(steps-1)*sides;triangles.append([end,end+side,end+side+1])
 strand_ranges.append({'first':start,'count':len(vertices)-start,'kind':path['kind']})
verts=np.asarray(vertices,dtype='f4');faces=np.asarray(triangles,dtype='u2')
conversion=np.array([[1,0,0],[0,0,-1],[0,1,0]])
mesh=bpy.data.meshes.new('Hair42_Filaments');mesh.from_pydata((verts@conversion.T).tolist(),[],faces.tolist());mesh.update()
for poly in mesh.polygons:poly.use_smooth=True
normal=np.array([v.normal[:] for v in mesh.vertices])@conversion
# Barycentric nearest-surface weight transfer, maintaining the source rig.
hj=a.arr(hp['attributes']['JOINTS_0']).copy();hw=a.arr(hp['attributes']['WEIGHTS_0']).copy();joints=[];weights=[];transfer=[]
for point in verts:
 hit,_,index,distance=hair_bvh.find_nearest(Vector(point));corners=new[tri[index]]
 bary=np.linalg.lstsq(np.vstack([corners.T,np.ones(3)]),np.r_[hit[:],1],rcond=None)[0];bary=np.maximum(bary,0);bary/=bary.sum();acc={}
 for source,b in zip(tri[index],bary):
  for joint,weight in zip(hj[source],hw[source]):acc[int(joint)]=acc.get(int(joint),0)+float(b*weight)
 chosen=sorted(acc.items(),key=lambda x:-x[1])[:4];chosen+=[(0,0)]*(4-len(chosen));j,wg=zip(*chosen);wg=np.array(wg);wg/=wg.sum();joints.append(j);weights.append(wg);transfer.append(float(distance))
np.savez(root/'work/hair42-filaments.npz',POSITION=verts,NORMAL=normal.astype('f4'),COLOR_0=np.array(colors,dtype='f4'),JOINTS_0=np.array(joints,dtype='u2'),WEIGHTS_0=np.array(weights,dtype='f4'),indices=faces)
report={'baseline':'v41','crown_vertices_moved':int(changed.sum()),'crown_max_displacement_mm':float(np.linalg.norm(new-old,axis=1).max()*1000),'face_seam_displacement_mm':float(np.linalg.norm(delta[shared],axis=1).max()*1000),'original_triangles':len(tri),'filaments':len(paths),'fringe_filaments':28,'crown_filaments':10,'filament_triangles':len(faces),'filament_vertices':len(verts),'nearest_hair_transfer_max_mm':max(transfer)*1000,'strand_ranges':strand_ranges,'paths':paths}
(root/'work/hair42-build.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['strand_ranges','paths']}))
