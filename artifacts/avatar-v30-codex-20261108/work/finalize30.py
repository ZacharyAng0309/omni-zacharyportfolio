import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
with bpy.data.libraries.load(str(root/'work/hand30-review.blend'),link=False) as (available,loaded):
    loaded.scenes=['Hand articulation review v30']
hand=bpy.data.scenes['Hand articulation review v30'];hand.use_fake_user=True
bpy.context.window.scene=hand
hand.frame_set(1)
hand.camera.location=Vector((-.389,-.068,.827))+Vector((-1,0,0))
hand.camera.rotation_euler=(Vector((-.389,-.068,.827))-hand.camera.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.data.scenes['Whole model review v30'];scene.use_fake_user=True
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
for name,frame in [('Neutral',1),('Adjust glasses',41),('Inspect tablet',81),('Present',121)]:scene.timeline_markers.new(name,frame=frame)
scene.frame_set(1);bpy.context.window.scene=scene
bpy.ops.wm.save_as_mainfile(filepath=str(root/'outputs/Zachary_Avatar_v30_Review.blend'),compress=True)
