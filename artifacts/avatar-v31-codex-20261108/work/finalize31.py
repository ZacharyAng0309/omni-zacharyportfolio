import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with bpy.data.libraries.load(str(root/'work/face31-review.blend'),link=False) as (available,loaded):
    loaded.scenes=['Facial expression review v31']
face_scene=bpy.data.scenes['Facial expression review v31'];face_scene.use_fake_user=True;face_scene.frame_set(1)
scene=bpy.data.scenes['Whole model review v31'];scene.use_fake_user=True
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
for name,frame in [('Neutral',1),('Adjust glasses',41),('Inspect tablet',81),('Present',121)]:scene.timeline_markers.new(name,frame=frame)
scene.frame_set(1);bpy.context.window.scene=face_scene
bpy.ops.wm.save_as_mainfile(filepath=str(root/'outputs/Zachary_Avatar_v31_Review.blend'),compress=True)
