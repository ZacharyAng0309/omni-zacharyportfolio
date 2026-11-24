"""Inspect existing hand shape and joint locations in Blender, without asset edits."""
import bpy, sys, json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
from kinematics27 import world
asset=Asset(root/'outputs/zachary_character_v27_candidate.glb')
scene=bpy.context.scene
for obj in list(scene.objects): bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(asset.path))
for obj in scene.objects:
    if obj.type=='MESH': obj.hide_render=not obj.name.startswith('SM_Character_Hands')
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=800; scene.render.resolution_y=800; scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Hand review world'); scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
def convert(point): return Vector((point[0],-point[2],point[1]))
target=convert((-.389,.822,.068))
camera=bpy.data.objects.new('CAM_Hand',bpy.data.cameras.new('CAM_Hand')); scene.collection.objects.link(camera); scene.camera=camera
camera.data.type='ORTHO'; camera.data.ortho_scale=.20
for name,offset,energy in [('Key',(-1,-1,1),55),('Fill',(1,0,.5),35)]:
    data=bpy.data.lights.new('LGT_'+name,'AREA'); data.energy=energy; data.size=1.2
    obj=bpy.data.objects.new(data.name,data); scene.collection.objects.link(obj); obj.location=target+Vector(offset)
    obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
for label,offset in [('front',(0,0,1)),('back',(0,0,-1)),('outer',(-1,0,0)),('inner',(1,0,0))]:
    camera.location=target+convert(offset)
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'work/hand28-{label}.png'); bpy.ops.render.render(write_still=True)
positions={name:matrix[:3,3].tolist() for name,matrix in world(node_data=asset.g['nodes']).items() if 'Hand' in name}
(root/'work/hand28-joints.json').write_text(json.dumps(positions,indent=2))
