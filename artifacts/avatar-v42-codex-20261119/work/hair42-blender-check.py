"""Reopened Blender: imported strand colors, topology and head-following behavior."""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector,Quaternion
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v42_candidate.glb');scene=bpy.data.scenes['Facial expression review v42'];bpy.context.window.scene=scene;scene.frame_set(1)
rig=next(o for o in scene.objects if o.type=='ARMATURE');hair=next(o for o in scene.objects if o.name.startswith('SM_Character_HairFilaments'))
assert sum(len(p.vertices)-2 for p in hair.data.polygons)==2360
assert len(hair.data.color_attributes)==1
shader=next(n for n in hair.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
assert shader.inputs['Base Color'].is_linked and shader.inputs['Alpha'].default_value==1
modifier=next(m for m in hair.modifiers if m.type=='ARMATURE');assert modifier.object==rig
bpy.context.view_layer.update();head=rig.pose.bones['Head'];original=head.matrix_basis.copy();rest=(rig.matrix_world@head.matrix).copy()
def evaluated():
 ob=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ob.to_mesh();p=np.array([ob.matrix_world@v.co for v in mesh.vertices]);ob.to_mesh_clear();return p
base=evaluated();report={'filament_triangles':2360,'imported_filament_vertices':len(base),'head_rotation_checks':{}}
for name,axis,angle in [('yaw_left',(0,0,1),-.45),('yaw_right',(0,0,1),.45),('pitch',(1,0,0),.25)]:
 head.matrix_basis=original@Quaternion(axis,angle).to_matrix().to_4x4();bpy.context.view_layer.update();delta=(rig.matrix_world@head.matrix)@rest.inverted()
 expected=np.array([delta@Vector(p) for p in base]);actual=evaluated();error=float(np.linalg.norm(expected-actual,axis=1).max()*1000)
 assert error<.002,(name,error);report['head_rotation_checks'][name]={'checked_vertices':len(base),'maximum_error_mm':error}
head.matrix_basis=original;bpy.context.view_layer.update()
# Numeric distances use the exported guide positions and raised-brow source surface.
from mathutils.bvhtree import BVHTree
fp=a.prim('SM_Character_Face');f=a.pos('SM_Character_Face').copy();fm=next(m for m in a.g['meshes'] if m['name']=='SM_Character_Face');index=fm['extras']['targetNames'].index('browInnerUp');f+=a.arr(fp['targets'][index]['POSITION'])
tri=a.arr(fp['indices']).reshape(-1,3);tree=BVHTree.FromPolygons([Vector(p) for p in f],tri.tolist(),all_triangles=True)
build=json.loads((root/'work/hair42-build.json').read_text());minimum=1;sampled=0
for strand in build['paths']:
 if strand['kind']!='fringe':continue
 centers=np.array(strand['centers']);n=len(centers)
 for j in range(n-1):
  for t in [0,.25,.5,.75]:
   progress=(j+t)/(n-1)
   if progress<.62:continue
   p=centers[j]*(1-t)+centers[j+1]*t;hit=tree.ray_cast(Vector((p[0],p[1],.4)),Vector((0,0,-1)))[0]
   if hit is not None:minimum=min(minimum,p[2]-hit.z-strand['radius']);sampled+=1
assert minimum>-.00005,minimum
report['raised_brow_distal_fringe_samples']=sampled;report['conservative_minimum_forehead_clearance_mm']=minimum*1000
(root/'work/hair42-blender-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
