import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Whole model review v31'];bpy.context.window.scene=scene
rig=next(obj for obj in scene.objects if obj.type=='ARMATURE');errors={}
for frame,targets in {41:{'RightHand':(-.18,1.51,.13)},81:{'RightHand':(-.21,1.12,.24),'LeftHand':(.21,1.12,.24)},121:{'RightHand':(-.37,1.20,.24)}}.items():
    scene.frame_set(frame);bpy.context.view_layer.update();row={}
    for name,(x,y,z) in targets.items():
        error=(rig.matrix_world@rig.pose.bones[name].head-Vector((x,-z,y))).length*1000
        assert error<.1;row[name]=error
    errors[str(frame)]=row
facial=bpy.data.scenes['Facial expression review v31'];bpy.context.window.scene=facial
face=next(o for o in facial.objects if o.type=='MESH' and o.data.shape_keys)
expected={1:(0,0),41:(.5,.5),81:(1,1),121:(1,0),161:(1,1)}
values={}
for frame,pair in expected.items():
    facial.frame_set(frame);bpy.context.view_layer.update()
    actual=tuple(face.data.shape_keys.key_blocks[name].value for name in ['eyeBlinkLeft','eyeBlinkRight'])
    assert max(abs(a-b) for a,b in zip(actual,pair))<1e-6
    values[str(frame)]=actual
images=set()
for review_scene in [scene,facial]:
    for obj in review_scene.objects:
        if obj.type!='MESH':continue
        for material in obj.data.materials:
            images.update(node.image for node in material.node_tree.nodes if node.type=='TEX_IMAGE' and node.image)
assert all(image.packed_file for image in images)
report={'reopened_gesture_errors_mm':errors,'reopened_blink_weights':values,
        'packed_image_datablocks':len(images),'retained_review_scenes':[scene.name,facial.name]}
(root/'work/blend31-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
