import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
with bpy.data.libraries.load(str(root/'work/hand28-review.blend'),link=False) as (available,loaded):
    loaded.scenes=['Hand articulation review v28']
hand=bpy.data.scenes['Hand articulation review v28'];hand.use_fake_user=True
bpy.context.window.scene=hand
target=Vector((.386,-.068,.827))
for curl,frame in [(0,1),(.35,81)]:
    hand.frame_set(frame)
    for name,offset in [('outer',(1,0,0)),('front',(0,-1,0))]:
        hand.camera.location=target+Vector(offset)
        hand.camera.rotation_euler=(target-hand.camera.location).to_track_quat('-Z','Y').to_euler()
        hand.render.filepath=str(root/f'work/hand-v28-left-{curl:.2f}-{name}.png')
        bpy.ops.render.render(write_still=True)
hand.frame_set(1)
hand.camera.location=Vector((-.389,-.068,.827))+Vector((-1,0,0))
hand.camera.rotation_euler=(Vector((-.389,-.068,.827))-hand.camera.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.data.scenes['Whole model review v28'];scene.use_fake_user=True
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
for name,frame in [('Neutral',1),('Adjust glasses',41),('Inspect tablet',81),('Present',121)]:scene.timeline_markers.new(name,frame=frame)
scene.frame_set(1);bpy.context.window.scene=scene
bpy.ops.wm.save_as_mainfile(filepath=str(root/'outputs/Zachary_Avatar_v28_Review.blend'),compress=True)
