import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parents[1]; out=r/'outputs'; stats={}
for version in (22,23):
 s=bpy.data.scenes.new('Portrait review v'+str(version));bpy.context.window.scene=s;s.unit_settings.system='METRIC'
 bpy.ops.import_scene.gltf(filepath=str(out/f'zachary_character_v{version}_candidate.glb'))
 def find(name):return next(o for o in s.objects if o.name.startswith(name))
 glass=find('Sovereign_Titanium_Spectacles')
 dg=bpy.context.evaluated_depsgraph_get()
 def geo(o):
  e=o.evaluated_get(dg);mesh=e.to_mesh();verts=[e.matrix_world@v.co for v in mesh.vertices];polys=[tuple(f.vertices) for f in mesh.polygons]; e.to_mesh_clear();return verts,polys,BVHTree.FromPolygons(verts,polys,all_triangles=True)
 gp,gt,gb=geo(glass);row={}
 for name in ['SM_Character_Face','SM_Character_Hair']:
  pts,fs,tree=geo(find(name)); overlaps=gb.overlap(tree)
  row[name]={'overlapping_triangle_pairs':len(overlaps),'locations':[[round(z,3) for z in gp[gt[k][0]]] for k,j in overlaps[::max(1,len(overlaps)//8)][:10]]}
  if name.endswith('Face'):
   for side in [-1,1]:
    ear=[v for v in pts if side*v.x>.072 and 1.53<v.z<1.625 and -.028<v.y<.045]
    row[str(side)]={'ear_region_vertical_span_mm':round(1000*(max(p.z for p in ear)-min(p.z for p in ear)),2),'outermost_mm':round(1000*max(p.x*side for p in ear),2)}
 stats[version]=row
 s.world=bpy.data.worlds.new('Soft grey');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.5
 s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=720;s.render.resolution_y=720;s.render.resolution_percentage=100
 cam=bpy.data.objects.new('Portrait camera',bpy.data.cameras.new('Portrait camera'));s.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.36
 for label,loc,power,size in [('Key',(-1,-2,2.5),100,1.5),('Fill',(1,-1,1.8),60,1.5),('Rim',(0,1,2.2),90,1)]:
  l=bpy.data.lights.new(label,'AREA');l.energy=power;l.size=size;l.shape='DISK';o=bpy.data.objects.new(label,l);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
 for label,loc in [('front',(0,-3,1.585)),('quarter',(1.45,-2.62,1.585)),('left',(-2.9,-.5,1.585)),('right',(2.9,-.5,1.585))]:
  cam.location=loc;cam.rotation_euler=(Vector((0,0,1.585))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/f'fit-v{version}-{label}.png');bpy.ops.render.render(write_still=True)
 cam.location=(0,-3,1.585);cam.rotation_euler=(Vector((0,0,1.585))-cam.location).to_track_quat('-Z','Y').to_euler()
 for a in bpy.context.screen.areas:
  if a.type=='VIEW_3D': a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False
 (r/'work/fit23-measurements.json').write_text(json.dumps(stats,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Zachary_Avatar_v23_Review.blend'),compress=True)
print('FIT CHECK',json.dumps(stats))
