"""Render a supplied GLB with the established portrait review lighting."""
import bpy
import sys
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
arguments = sys.argv[sys.argv.index('--') + 1:]
source = root / arguments[0]
prefix = arguments[1]
scene = bpy.data.scenes.new('Portrait review v39')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
bpy.ops.import_scene.gltf(filepath=str(source))
scene.world = bpy.data.worlds.new('Soft grey')
scene.world.use_nodes = True
background = scene.world.node_tree.nodes['Background']
background.inputs[0].default_value = (.18, .18, .18, 1)
background.inputs[1].default_value = .5
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 720
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
camera = bpy.data.objects.new('CAM_Portrait', bpy.data.cameras.new('CAM_Portrait'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .36
target = Vector((0, 0, 1.585))
for name, location, energy, size in [
    ('Key', (-1, -2, 2.5), 100, 1.5),
    ('Fill', (1, -1, 1.8), 60, 1.5),
    ('Rim', (0, 1, 2.2), 90, 1),
]:
    light = bpy.data.lights.new('LGT_' + name, 'AREA')
    light.energy = energy
    light.size = size
    light.shape = 'DISK'
    obj = bpy.data.objects.new(light.name, light)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0, 0, 1.5)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
views = [('front', (0, -3, 1.585)), ('quarter', (1.45, -2.62, 1.585)), ('left', (-2.9, -.5, 1.585)), ('top', (.1, -2, 3)), ('back', (0, 3, 1.65))]
if '--full' in arguments:
    views += [('left', (-2.9, -.5, 1.585)), ('right', (2.9, -.5, 1.585))]
if '--prepare-only' in arguments:
    views = []
for label, location in views:
    camera.location = location
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(root / f'{prefix}-{label}.png')
    bpy.ops.render.render(write_still=True)
camera.location = (0, -3, 1.585)
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
        area.spaces.active.overlay.show_overlays = False
review_path = root / f'{prefix}.blend'
if '--full' in arguments:
    with bpy.data.libraries.load(str(root / 'outputs/Zachary_Avatar_v26_Review.blend'), link=False) as (available, loaded):
        loaded.scenes = ['Portrait review v26']
    review_path = root / 'outputs/Zachary_Avatar_v39_Review.blend'
    bpy.context.window.scene = scene
bpy.ops.wm.save_as_mainfile(filepath=str(review_path), compress=True)


