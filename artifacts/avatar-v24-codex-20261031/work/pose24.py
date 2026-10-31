import bpy,json,math
from mathutils.bvhtree import BVHTree
from pathlib import Path
r=Path(__file__).resolve().parents[1];s=bpy.data.scenes['Portrait review v24'];bpy.context.window.scene=s
def find(prefix):return next(o for o in s.objects if o.name.startswith(prefix))
face=find('SM_Character_Face');hair=find('SM_Character_Hair');glass=find('Sovereign_Titanium_Spectacles');rig=next(o for o in s.objects if o.type=='ARMATURE')
def evaluated(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();pts=[e.matrix_world@v.co for v in mesh.vertices];fs=[tuple(f.vertices) for f in mesh.polygons];e.to_mesh_clear();return pts,BVHTree.FromPolygons(pts,fs,all_triangles=True)
from statistics import median
result={}
for label,keys,angle in [('neutral',[],0),('blink',['eyeBlinkLeft','eyeBlinkRight'],0),('smile',['mouthSmileLeft','mouthSmileRight'],0),('turn-left',[],15),('turn-right',[],-15)]:
 for k in face.data.shape_keys.key_blocks:k.value=float(k.name in keys)
 bone=rig.pose.bones['Head'];bone.rotation_mode='XYZ';bone.rotation_euler.y=math.radians(angle);bpy.context.view_layer.update()
 gp,gt=evaluated(glass);fp,ft=evaluated(face);hp,ht=evaluated(hair)
 result[label]={'face_pairs':len(gt.overlap(ft)),'hair_pairs':len(gt.overlap(ht))}
 if label=='neutral':
  for side in [-1,1]:
   for region,lo,hi in [('shaft',.015,.055),('support',-.025,-.005)]:
    d=[min(ft.find_nearest(v)[3],ht.find_nearest(v)[3])*1000 for v in gp if v.x*side>.060 and lo< -v.y<hi]
    if d:result[label][region+str(side)]={'sampled_surface_gap_mm_min':round(min(d),2),'median':round(median(d),2)}
print(json.dumps(result));(r/'work/ear24-pose.json').write_text(json.dumps(result,indent=2))
