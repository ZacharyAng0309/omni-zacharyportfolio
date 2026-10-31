import bpy,json
from mathutils import Vector
baseline=bpy.data.scenes['Zachary_Refinement_v21']
scene=bpy.data.scenes.new('Zachary_v22_Candidate')
scene.unit_settings.system='METRIC'
bpy.context.window.scene=scene
scene.world=baseline.world
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.resolution_x=720; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
for o in baseline.objects:
 if o.type in ['LIGHT','CAMERA']:
  new=o.copy(); new.data=o.data.copy(); scene.collection.objects.link(new)
  if o.type=='CAMERA': scene.camera=new
bpy.ops.import_scene.gltf(filepath=r'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\zachary_character_v22_candidate.glb')
for view,loc in [('front',(0,-3,1.55)),('quarter',(2.3,-2.3,1.55)),('side',(3,0,1.55))]:
 scene.camera.location=loc; scene.camera.rotation_euler=(Vector((0,0,1.55))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=rf'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\avatar-v22-{view}.png'
 bpy.ops.render.render(write_still=True)
scene.camera.location=(0,-3,1.55); scene.camera.rotation_euler=(Vector((0,0,1.55))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'; area.spaces.active.shading.type='MATERIAL'
print('Candidate loaded; baseline retained as separate scene.')
