import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Whole model review v29'];bpy.context.window.scene=scene
rig=next(obj for obj in scene.objects if obj.type=='ARMATURE')
report={}
for frame,targets in {41:{'RightHand':(-.18,1.51,.13)},81:{'RightHand':(-.21,1.12,.24),'LeftHand':(.21,1.12,.24)},121:{'RightHand':(-.37,1.20,.24)}}.items():
    scene.frame_set(frame);bpy.context.view_layer.update()
    errors={}
    for name,(x,y,z) in targets.items():
        error=(rig.matrix_world@rig.pose.bones[name].head-Vector((x,-z,y))).length*1000
        assert error<.1;(errors.update({name:error}))
    report[str(frame)]=errors
hand=bpy.data.scenes['Hand articulation review v29'];bpy.context.window.scene=hand
handrig=next(obj for obj in hand.objects if obj.type=='ARMATURE')
positions={}
for frame in [1,41,81,121]:
    hand.frame_set(frame);bpy.context.view_layer.update()
    positions[str(frame)]=list(handrig.matrix_world@handrig.pose.bones['RightHandIndex3'].head)
assert (Vector(positions['1'])-Vector(positions['81'])).length>.005
images=set()
for review_scene in [scene,hand]:
    for obj in review_scene.objects:
        if obj.type!='MESH':continue
        for material in obj.data.materials:
            images.update(node.image for node in material.node_tree.nodes if node.type=='TEX_IMAGE' and node.image)
assert all(image.packed_file for image in images)
result={'reopened_gesture_wrist_errors_mm':report,'finger_review_frames':[1,41,81,121],
        'finger_motion_verified':True,'packed_image_datablocks':len(images),'retained_review_scenes':[scene.name,hand.name]}
(root/'work/blend29-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
