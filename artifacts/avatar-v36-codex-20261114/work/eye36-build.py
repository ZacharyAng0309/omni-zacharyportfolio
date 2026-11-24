"""Author fitted eyelid loops and separate eyes; bake existing skin color in Blender."""
import bpy,sys,math,json,copy,io
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v35_candidate.glb');p=a.prim('SM_Character_Face')
attrs={k:a.arr(i).copy() for k,i in p['attributes'].items()};oldtargets=[a.arr(t['POSITION']).copy() for t in p['targets']];x=attrs['POSITION'];tri=a.arr(p['indices']).reshape(-1,3).copy()
tree=BVHTree.FromPolygons([Vector(v) for v in x],tri.tolist(),all_triangles=True)
def sample(q):
 hit,n,index,dist=tree.ray_cast(Vector((float(q[0]),float(q[1]),.3)),Vector((0,0,-1)),.6);assert hit is not None
 row=tri[index];v=x[row];xy=v[:,:2];weights=np.linalg.solve(np.vstack([xy.T,np.ones(3)]),[q[0],q[1],1]);return np.array(hit),row,weights
def inside(q,poly):
 count=0
 for i,v in enumerate(poly):
  u=poly[i-1]
  if (v[1]>q[1])!=(u[1]>q[1]) and q[0]<(u[0]-v[0])*(q[1]-v[1])/(u[1]-v[1])+v[0]:count+=1
 return count%2==1
eye_specs={sign:float(sample([sign*.034,1.598])[0][2]-.010) for sign in [-1,1]}
# Existing outer lids also need depth motion to travel over the globe.
for sign in [-1,1]:
 k=4 if sign==1 else 5;d=oldtargets[k];moving=np.linalg.norm(d,axis=1)>1e-8
 for alpha in [.25,.5,.75,1.]:
  q=x+d*alpha;dx=q[:,0]-sign*.034;dy=q[:,1]-1.598;r=1-(dx/.017)**2-(dy/.012)**2;valid=(r>0)&moving
  desired=eye_specs[sign]+.0105*np.sqrt(np.maximum(r,0))-sign*.22*dx+.00065
  d[valid,2]=np.maximum(d[valid,2],(desired[valid]-x[valid,2])/alpha)
points=[];bake_points=[];normals=[];weights=[];joints=[];morphs=[[] for _ in range(8)];faces=[];quad_starts=[];rings_report=[];remove=np.zeros(len(tri),bool);eye_data=[]
N=32;angles=np.arange(N)*2*np.pi/N
def append(point,row,bc,deltas=None,normal=None,bake_point=None):
 i=len(points);points.append(np.array(point));bake_points.append(np.array(point if bake_point is None else bake_point));normals.append(attrs['NORMAL'][row].T@bc if normal is None else normal)
 accum={}
 for source,weight in zip(row,bc):
  for joint,blend in zip(attrs['JOINTS_0'][source],attrs['WEIGHTS_0'][source]):accum[int(joint)]=accum.get(int(joint),0)+float(weight*blend)
 top=sorted(accum.items(),key=lambda v:v[1],reverse=True)[:4];top+=[(0,0)]*(4-len(top));w=np.maximum([v for j,v in top],0);w/=sum(w);joints.append([j for j,v in top]);weights.append(w)
 for k in range(8):morphs[k].append(oldtargets[k][row].T@bc if deltas is None else deltas[k])
 return i
for sign in [-1,1]:
 r=np.load(root/f'work/eye36-patch{sign}.npz');remove|=r['mask'];loop=r['loop'];gp=r['points'];sources=r['source_ids'];center=np.array([sign*.034,1.598]);zcenter=eye_specs[sign];rx,ry,rz=.017,.012,.0105;slope=-sign*.22
 def globe(q):
  dx,dy=q-center;return zcenter+rz*math.sqrt(max(.001,1-(dx/rx)**2-(dy/ry)**2))+slope*dx
 boundary=[]
 for geo in loop:
  source=int(sources[geo]);boundary.append(append(gp[geo],np.array([source]*3),np.array([1,0,0])))
 rings=[]
 for level,factor in enumerate([1.20,1.08,1.0,.99]):
  ring=[]
  for angle in angles:
   source_q=center+np.array([.014*factor*math.cos(angle),.005*factor*math.sin(angle)])
   q=center+np.array([.014*factor*math.cos(angle),.005*factor*[1,.9,.76,.76][level]*math.sin(angle)])
   surf,row,bc=sample(source_q);g=globe(q)
   z=surf[2]*.65+(g+.0005)*.35 if level==0 else g+(.0006 if level<3 else -.0001)
   point=np.r_[q,z];d=[oldtargets[k][row].T@bc for k in range(8)];d[6]*=[.85,.4,0,0][level];blink=4 if sign==1 else 5
   closed_y=center[1]+.00005*math.sin(angle);qclosed=np.array([q[0],closed_y]);closed_z=globe(qclosed)+(.0006 if level<3 else -.0001)
   influence=[.35,.75,1.,1.][level]
   d[blink]=(1-influence)*d[blink]+influence*np.array([0,closed_y-q[1],closed_z-z])
   for alpha in [.25,.5,.75,1.]:
    posed=point+d[blink]*alpha;dx,dy=posed[:2]-center
    if (dx/rx)**2+(dy/ry)**2<1:d[blink][2]=max(d[blink][2],(globe(posed[:2])+.00065-point[2])/alpha)
   ring.append(append(point,row,bc,d,bake_point=surf));
  rings.append(ring)
 # Constrained triangle bridge keeps the original irregular socket boundary.
 xy=[Vector(points[i][:2]) for i in boundary+rings[0]];nb=len(boundary);edges=[(i,(i+1)%nb) for i in range(nb)]+[(nb+i,nb+(i+1)%N) for i in range(N)]
 result=delaunay_2d_cdt(xy,edges,[list(range(nb))],1,1e-8,True);vv,ee,ff,orig,_,_=result
 assert all(len(v)==1 for v in orig),'Socket rings intersect the original boundary'
 mapping=[(boundary+rings[0])[v[0]] for v in orig];inner=np.array([points[i][:2] for i in rings[0]])
 for f in ff:
  row=[mapping[i] for i in f];c=np.mean([points[i][:2] for i in row],0)
  if inside(c,inner):continue
  if np.cross(points[row[1]]-points[row[0]],points[row[2]]-points[row[0]])[2]<0:row=[row[0],row[2],row[1]]
  faces.append(row)
 for outer,inner in zip(rings[:-1],rings[1:]):
  for j in range(N):
   k=(j+1)%N
   quad_starts.append(len(faces))
   for row in [[outer[j],outer[k],inner[k]],[outer[j],inner[k],inner[j]]]:
    if np.cross(points[row[1]]-points[row[0]],points[row[2]]-points[row[0]])[2]<0:row=[row[0],row[2],row[1]]
    faces.append(row)
 rings_report.append({'sign':sign,'boundary_indices':boundary,'rings':rings,'zcenter':float(zcenter)})
 # Separate closed globe, with semantic pupil/iris/sclera vertex colors.
 ep=[np.r_[center,zcenter+rz]];colors=[[.002,.0015,.001]];et=[];ering=[]
 for rr in [.0025,.0040,.0053,.0056]:
  ring=[]
  for angle in angles:
   q=center+rr*np.array([math.cos(angle),math.sin(angle)]);ring.append(len(ep));ep.append(np.r_[q,globe(q)])
   variation=.8+.2*math.sin(angle*13+.6)**2
   color=np.array([.034,.014,.006])*variation if rr<=.0053 else np.array([.012,.007,.004])
   if rr==.0025:color=np.array([.002,.0015,.001])
   colors.append(color)
  ering.append(ring)
 for phi in [.65,1.10,np.pi/2,2.1,2.65]:
  ring=[]
  for angle in angles:
   dx=rx*math.sin(phi)*math.cos(angle);dy=ry*math.sin(phi)*math.sin(angle);ring.append(len(ep));ep.append([center[0]+dx,center[1]+dy,zcenter+rz*math.cos(phi)+slope*dx]);colors.append([.32,.30,.28])
  ering.append(ring)
 back=len(ep);ep.append([center[0],center[1],zcenter-rz]);colors.append([.32,.30,.28])
 for j in range(N):
  k=(j+1)%N;et.append([0,ering[0][j],ering[0][k]]);et.append([back,ering[-1][k],ering[-1][j]])
 for r0,r1 in zip(ering[:-1],ering[1:]):
  for j in range(N):
   k=(j+1)%N;et.extend([[r0[j],r1[j],r1[k]],[r0[j],r1[k],r0[k]]])
 eye_data.append((sign,np.array(ep),np.array(et),np.array(colors)))
points=np.array(points,dtype='f4').astype(float);faces=np.array(faces);morphs=np.array(morphs)
# Keep closed loops nested. Texture-transfer sample positions must not dictate
# the smaller neutral lid's closure distance.
for side in rings_report:
 k=4 if side['sign']==1 else 5;rings=side['rings'];outer=rings[0]
 outer_end=points[outer,1]+morphs[k,outer,1]-1.598
 outer_end=np.sign(np.sin(angles))*np.maximum(abs(outer_end),.00018*abs(np.sin(angles)))
 inner_end=np.zeros(N)
 for level,ring in enumerate(rings):
  end=outer_end if level==0 else (.4*outer_end+.6*inner_end if level==1 else inner_end)
  morphs[k,ring,1]=(np.asarray(1.598+end,dtype='f4')-points[ring,1].astype('f4')).astype(float)
  morphs[6,ring]=0
  if level>=2:
   dx=points[ring,0]-side['sign']*.034
   end_z=side['zcenter']+.0105*np.sqrt(np.maximum(.001,1-(dx/.017)**2))-side['sign']*.22*dx+(.00065 if level==2 else -.00025)
   morphs[k,ring,2]=(np.asarray(end_z,dtype='f4')-points[ring,2].astype('f4')).astype(float)
def min_front(rows):
 minimum=1
 for y in [points,points+morphs[4]+morphs[5],points+morphs[4]+morphs[5]+morphs[6]]:
  c=np.cross(y[rows[:,1]]-y[rows[:,0]],y[rows[:,2]]-y[rows[:,0]])
  minimum=min(minimum,float(c[:,2].min()))
 return minimum
for start in quad_starts:
 pair=faces[start:start+2]
 if min_front(pair)<-1e-12:
  oj,ok,ik=pair[0];ij=pair[1,2];alternative=np.array([[oj,ok,ij],[ok,ik,ij]])
  if min_front(alternative)>min_front(pair):faces[start:start+2]=alternative
def calculated_normals(pos,t):
 n=np.zeros_like(pos);c=np.cross(pos[t[:,1]]-pos[t[:,0]],pos[t[:,2]]-pos[t[:,0]])
 for k in range(3):np.add.at(n,t[:,k],c)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);return n
normal=calculated_normals(points,faces)
for row in rings_report:
 for i in row['boundary_indices']:normal[i]=normals[i]/np.linalg.norm(normals[i])
# Bake source face color onto the two unwrapped eyelid islands.
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(root/'outputs/zachary_character_v35_candidate.glb'));source=bpy.data.objects['SM_Character_Face']
conversion=np.array([[1,0,0],[0,0,-1],[0,1,0]]);mesh=bpy.data.meshes.new('GEO_Eyelids_v36');mesh.from_pydata((np.array(bake_points)@conversion.T).tolist(),[],faces.tolist());mesh.update();obj=bpy.data.objects.new('SM_Character_Eyelids',mesh);bpy.context.scene.collection.objects.link(obj)
for o in bpy.context.scene.objects:o.select_set(False)
obj.select_set(True);bpy.context.view_layer.objects.active=obj;mesh.uv_layers.new(name='UV_Eyelids')
for poly in mesh.polygons:poly.select=True;poly.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
image=bpy.data.images.new('T_Eyelids_v36',width=1024,height=1024,alpha=False);mat=bpy.data.materials.new('M_Eyelids_Bake');mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.nodes.active=node;mesh.materials.append(mat)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.006;scene.render.bake.max_ray_distance=.025;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=16
for o in scene.objects:
 if o.type=='MESH':o.hide_render=o not in [source,obj]
source.select_set(True);bpy.ops.object.bake(type='DIFFUSE');image.filepath_raw=str(root/'work/eye36-lids.png');image.file_format='PNG';image.save()
uv=np.zeros((len(points),2))
for poly in mesh.polygons:
 for vi,li in zip(poly.vertices,poly.loop_indices):uv[vi]=mesh.uv_layers.active.data[li].uv[:]
uv[:,1]=1-uv[:,1]
np.savez(root/'work/eye36-generated.npz',points=points,triangles=faces,normals=normal,uv=uv,weights=np.array(weights),joints=np.array(joints),morphs=morphs,removed=remove,face_blinks=np.array(oldtargets)[[4,5]])
for sign,ep,et,color in eye_data:
 ep[:,2]-=.0005
 # Ensure outward normals using signed volume before serializing.
 volume=np.sum(np.einsum('ij,ij->i',ep[et[:,0]],np.cross(ep[et[:,1]],ep[et[:,2]])))/6
 if volume<0:et=et[:,[0,2,1]]
 np.savez(root/f'work/eye36-globe{sign}.npz',points=ep,triangles=et,normals=calculated_normals(ep,et),colors=color)
(root/'work/eye36-rings.json').write_text(json.dumps(rings_report,indent=2));print('EYELID_BUILD',len(points),len(faces),'removed',int(sum(remove)))
