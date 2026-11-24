import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with bpy.data.libraries.load(str(root/'work/expression34.blend'),link=False) as (available,loaded):
    loaded.scenes=['Facial expression audit v34']
facial=bpy.data.scenes['Facial expression audit v34'];facial.name='Facial expression review v34';facial.use_fake_user=True;facial.frame_set(1)
whole=bpy.data.scenes['Whole model review v34'];whole.use_fake_user=True;whole.frame_set(1)
for marker in list(whole.timeline_markers):whole.timeline_markers.remove(marker)
for name,frame in [('Station',1),('Adjust glasses',41),('Inspect tablet',81),('Present',121)]:whole.timeline_markers.new(name,frame=frame)
bpy.context.window.scene=facial
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(root/'outputs/Zachary_Avatar_v34_Review.blend'),compress=True)
