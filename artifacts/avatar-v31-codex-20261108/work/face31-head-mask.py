import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Facial expression audit v30'];bpy.context.window.scene=scene;scene.frame_set(1)
for obj in scene.objects:
    if obj.type=='MESH' and obj.name.startswith(('SM_Cloth_','SM_Character_Hands')):obj.hide_render=True
scene.render.film_transparent=True;scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.render.filepath=str(root/'work/face31-head-transparent.png');bpy.ops.render.render(write_still=True)
