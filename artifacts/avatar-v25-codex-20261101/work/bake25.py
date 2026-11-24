"""Bake diffuse color and strand normals into the repacked hair islands."""
import bpy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
scene = bpy.data.scenes['Portrait review v25']
bpy.context.window.scene = scene
hair = next(obj for obj in scene.objects if obj.name.startswith('SM_Character_Hair'))
tree = hair.data.materials[0].node_tree
original_uv = hair.data.uv_layers[0]
uv_node = tree.nodes.new('ShaderNodeUVMap')
uv_node.uv_map = original_uv.name
for node in tree.nodes:
    if node.type == 'TEX_IMAGE':
        tree.links.new(uv_node.outputs[0], node.inputs['Vector'])
rows = json.loads((root / 'work/hair25-uv.json').read_text())
lookup = {tuple(round(value, 6) for value in row['position'] + row['old_uv']): row['new_uv'] for row in rows}
packed_uv = hair.data.uv_layers.new(name='UV_Hair_Detail')
for loop in hair.data.loops:
    position = hair.data.vertices[loop.vertex_index].co[:]
    old = original_uv.data[loop.index].uv[:]
    key = tuple(round(value, 6) for value in position + old)
    packed_uv.data[loop.index].uv = lookup[key]
hair.data.uv_layers.active = packed_uv
packed_uv.active_render = True
for obj in scene.objects:
    obj.select_set(False)
hair.select_set(True)
bpy.context.view_layer.objects.active = hair
scene.cycles.samples = 8
scene.render.bake.use_selected_to_active = False
scene.render.bake.margin = 6
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False
scene.render.bake.use_pass_color = True
scene.render.bake.normal_space = 'TANGENT'
report = {}
for label, kind, resolution, image_format, extension in [
    ('albedo', 'DIFFUSE', 2048, 'WEBP', 'webp'),
    ('normal', 'NORMAL', 512, 'PNG', 'png'),
]:
    scene.render.bake.margin = 3 if label == 'normal' else 12
    image = bpy.data.images.new('T_Hair_v25_' + label, width=resolution, height=resolution, alpha=False)
    image.colorspace_settings.name = 'Non-Color' if label == 'normal' else 'sRGB'
    target = tree.nodes.new('ShaderNodeTexImage')
    target.image = image
    for node in tree.nodes:
        node.select = False
    target.select = True
    tree.nodes.active = target
    bpy.ops.object.bake(type=kind)
    path = root / f'work/hair25-{label}.{extension}'
    image.file_format = image_format
    image.filepath_raw = str(path)
    image.save()
    report[label] = {'resolution': resolution, 'bytes': path.stat().st_size}
(root / 'work/hair25-bake.json').write_text(json.dumps(report, indent=2))
print('BAKE_REPORT', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(root / 'work/hair25-baked.blend'), compress=True)
