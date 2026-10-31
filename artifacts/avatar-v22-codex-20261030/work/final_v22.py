import bpy,json
from mathutils import Vector
from pathlib import Path
if bpy.data.scenes.get('Zachary_v22_Candidate'): bpy.data.scenes['Zachary_v22_Candidate'].name='Zachary_v22_HairAuthoring'
exec(compile(Path(r'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\work\load_v22.py').read_text(),'load_v22.py','exec'))
scene=bpy.context.scene
face=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith('SM_Character_Face'))
for label,loc,target,scale in [('ear',(3,-0.8,1.575),(0.078,0,1.571),0.13),('ear-left',(-3,-0.8,1.575),(-0.078,0,1.571),0.13),('top',(0,-0.2,4),(0,0,1.6),0.36)]:
 scene.camera.location=loc; scene.camera.rotation_euler=(Vector(target)-scene.camera.location).to_track_quat('-Z','Y').to_euler(); scene.camera.data.ortho_scale=scale
 scene.render.filepath=rf'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\avatar-v22-{label}.png'; bpy.ops.render.render(write_still=True)
scene.camera.data.ortho_scale=0.43; scene.camera.location=(0,-3,1.55); scene.camera.rotation_euler=(Vector((0,0,1.55))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
for k in face.data.shape_keys.key_blocks: k.value=1 if k.name in ['eyeBlinkLeft','eyeBlinkRight'] else 0
scene.render.filepath=r'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\avatar-v22-blink.png'; bpy.ops.render.render(write_still=True)
for k in face.data.shape_keys.key_blocks: k.value=0
for image in bpy.data.images:
 if image.source=='FILE' and image.has_data and not image.packed_file:
  image.pack()
for o in scene.objects:o.select_set(False)
face.select_set(True); bpy.context.view_layer.objects.active=face
bpy.ops.wm.save_as_mainfile(filepath=r'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\Zachary_Avatar_v22_Review.blend')
print('Saved v22 review with packed textures and neutral expression.')
