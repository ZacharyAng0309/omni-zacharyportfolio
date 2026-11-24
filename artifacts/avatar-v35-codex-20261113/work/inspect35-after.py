import bpy
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];scene=bpy.context.scene
mat=bpy.data.materials.new('Diagnostic clay');mat.use_nodes=True
shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');shader.inputs['Base Color'].default_value=(.32,.32,.32,1);shader.inputs['Roughness'].default_value=.8
for o in scene.objects:
 if o.type=='MESH':
  if o.name.startswith(('SM_Character_Face','SM_Character_Hair')):o.data.materials.clear();o.data.materials.append(mat)
  else:o.hide_render=True
scene.camera.data.ortho_scale=.24;target=Vector((0,0,1.62));scene.render.resolution_x=800;scene.render.resolution_y=800;scene.cycles.samples=16
for name,loc in [('front',(0,-3,1.62)),('quarter',(1.45,-2.62,1.62))]:
 scene.camera.location=loc;scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(root/f'work/clay35-after-{name}.png');bpy.ops.render.render(write_still=True)
