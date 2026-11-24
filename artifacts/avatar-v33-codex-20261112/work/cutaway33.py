import bpy
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Facial expression audit v33'];bpy.context.window.scene=scene
scene.frame_set(161)
for obj in scene.objects:
    if obj.type=='MESH':obj.hide_render=not any(part in obj.name for part in ['UpperTeeth','LowerTeeth','Tongue'])
camera=scene.camera;camera.data.ortho_scale=.070
target=Vector((0,-.080,1.515));camera.location=(.055,-.23,1.59);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=800;scene.render.resolution_y=600;scene.cycles.samples=32
scene.render.filepath=str(root/'outputs/avatar-v33-oral-cutaway.png');bpy.ops.render.render(write_still=True)
