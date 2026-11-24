import bpy
import json
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
scene = bpy.data.scenes['Whole model review v27']
bpy.context.window.scene = scene
rig = next(obj for obj in scene.objects if obj.type == 'ARMATURE')
assert rig.animation_data and rig.animation_data.action
targets = {
    41: {'RightHand': (-.18, 1.51, .13)},
    81: {'RightHand': (-.21, 1.12, .24), 'LeftHand': (.21, 1.12, .24)},
    121: {'RightHand': (-.37, 1.20, .24)},
}
errors = {}
for frame, bones in targets.items():
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    row = {}
    for name, (x, y, z) in bones.items():
        actual = rig.matrix_world @ rig.pose.bones[name].head
        error = (actual - Vector((x, -z, y))).length * 1000
        assert error < .1, (frame, name, error)
        row[name] = error
    errors[str(frame)] = row
images = set()
for obj in scene.objects:
    if obj.type == 'MESH':
        for material in obj.data.materials:
            images.update(node.image for node in material.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image)
assert all(image.packed_file for image in images), 'Review textures must be embedded'
for marker in list(scene.timeline_markers):
    scene.timeline_markers.remove(marker)
for label, frame in [('Neutral', 1), ('Adjust glasses', 41), ('Inspect tablet', 81), ('Present', 121)]:
    scene.timeline_markers.new(label, frame=frame)
scene.frame_set(1)
scene.use_fake_user = True
with bpy.context.temp_override(scene=scene):
    bpy.ops.wm.save_as_mainfile(filepath=str(root / 'outputs/Zachary_Avatar_v27_Review.blend'), compress=True)
report = {'reopened_pose_errors_mm': errors, 'packed_texture_images': len(images),
          'review_frames': [1, 41, 81, 121], 'scene': scene.name}
(root / 'work/blend27-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
