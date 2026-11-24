"""Fresh Blender portrait and expression review of the exported v35 baseline."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
for obj in list(scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(root/'outputs/zachary_character_v35_candidate.glb'))
scene.name='Facial expression audit v35';scene.use_fake_user=True
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=720;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Portrait audit world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.20,.20,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
camera=bpy.data.objects.new('CAM_Portrait',bpy.data.cameras.new('CAM_Portrait'));scene.collection.objects.link(camera);scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=.30
target=Vector((0,0,1.595));camera.location=(0,-3,1.595);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
for name,location,energy,size in [('Key',(-1,-2,2.5),85,1.5),('Fill',(1,-1,1.8),55,1.5)]:
    data=bpy.data.lights.new('LGT_'+name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);obj.location=location
    obj.rotation_euler=(Vector((0,0,1.58))-obj.location).to_track_quat('-Z','Y').to_euler()
faces=[o for o in scene.objects if o.type=='MESH' and o.data.shape_keys];face=faces[0]
poses=[('neutral',{}),('blink',{'eyeBlinkLeft':1,'eyeBlinkRight':1}),
       ('smile',{'mouthSmileLeft':.42,'mouthSmileRight':.42}),('jaw',{'jawOpen':.45}),
       ('speech',{'viseme_aa':.65,'mouthOpen':.35}),('smile-speech',{'mouthSmileLeft':.42,'mouthSmileRight':.42,'viseme_aa':.65,'mouthOpen':.35}),('open',{'mouthOpen':1}),('wide',{'jawOpen':1,'mouthOpen':1}),('aa',{'viseme_aa':1}),('asymmetric-speech',{'mouthSmileLeft':.6,'mouthOpen':.4}),('half-blink',{'eyeBlinkLeft':.5,'eyeBlinkRight':.5}),('left-wink',{'eyeBlinkLeft':1}),('right-wink',{'eyeBlinkRight':1}),('blink-brow',{'eyeBlinkLeft':1,'eyeBlinkRight':1,'browInnerUp':1})]
for i,(label,values) in enumerate(poses):
    scene.frame_set(1+i*40)
    for face in faces:
        for key in face.data.shape_keys.key_blocks:
            key.value=values.get(key.name,0)
            if key.name!='Basis':key.keyframe_insert(data_path='value',frame=scene.frame_current)
    bpy.context.view_layer.update()
    scene.timeline_markers.new(label,frame=scene.frame_current)
    scene.render.filepath=str(root/f'work/expression35-{label}.png')
    if label in ['neutral','blink','half-blink','left-wink','right-wink','blink-brow']:bpy.ops.render.render(write_still=True)
scene.frame_set(161)
for label,location in [('speech-quarter',(1.3,-2.7,1.595)),('speech-side',(3,-.25,1.595))]:
    camera.location=location;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'work/expression35-{label}.png');bpy.ops.render.render(write_still=True)
camera.location=(0,-3,1.595);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
scene.frame_set(1);scene.frame_end=521
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/expression35.blend'),compress=True)
print(json.dumps({'shape_keys':list(face.data.shape_keys.key_blocks.keys()),'reviewed_poses':[name for name,values in poses]}))
