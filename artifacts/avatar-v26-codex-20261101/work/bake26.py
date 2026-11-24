"""Bake the continuous body colors and corrected hair regions for glTF."""
import bpy
import json
import numpy as np
from pathlib import Path

root = Path(__file__).resolve().parents[1]
scene = bpy.data.scenes['Portrait review v26']
bpy.context.window.scene = scene
face = next(obj for obj in scene.objects if obj.name.startswith('SM_Character_Face'))
hair = next(obj for obj in scene.objects if obj.name.startswith('SM_Character_Hair'))
mesh = bpy.data.meshes.new('AtlasBakeMesh')
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
uv = mesh.uv_layers.new(name=face.data.uv_layers[0].name)
for corner, coordinates in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
    corner.uv = coordinates
plane = bpy.data.objects.new('SM_AtlasBake', mesh)
scene.collection.objects.link(plane)
plane.data.materials.append(face.data.materials[0].copy())
hair.data.uv_layers.active_index = 1
hair.data.uv_layers[1].active_render = True
scene.cycles.samples = 8
scene.render.bake.use_selected_to_active = False
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False
scene.render.bake.use_pass_color = True
report = {}
for label, obj, kind, resolution in [
    ('body-albedo', plane, 'DIFFUSE', 2048),
    ('hair-albedo', hair, 'DIFFUSE', 2048),
    ('body-roughness', plane, 'EMIT', 1024),
    ('hair-roughness', hair, 'EMIT', 512),
]:
    for other in scene.objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    tree = obj.data.materials[0].node_tree
    if kind == 'EMIT':
        roughness = next(node for node in tree.nodes if node.label == 'V26_FINAL_ROUGHNESS').outputs[0]
        specular = next(node for node in tree.nodes if node.label == 'V26_FINAL_SPECULAR').outputs[0]
        channels = tree.nodes.new('ShaderNodeCombineColor')
        channels.mode = 'RGB'
        tree.links.new(specular, channels.inputs['Red'])
        channels.inputs['Blue'].default_value = 0
        tree.links.new(roughness, channels.inputs['Green'])
        emission = tree.nodes.new('ShaderNodeEmission')
        tree.links.new(channels.outputs[0], emission.inputs['Color'])
        output = next(node for node in tree.nodes if node.type == 'OUTPUT_MATERIAL')
        tree.links.new(emission.outputs[0], output.inputs['Surface'])
    image = bpy.data.images.new('T_v26_' + label, width=resolution, height=resolution, alpha=kind == 'EMIT')
    image.colorspace_settings.name = 'Non-Color' if kind == 'EMIT' else 'sRGB'
    if kind == 'EMIT':
        image.alpha_mode = 'CHANNEL_PACKED'
    target = tree.nodes.new('ShaderNodeTexImage')
    target.image = image
    for node in tree.nodes:
        node.select = False
    target.select = True
    tree.nodes.active = target
    scene.render.bake.margin = 3 if resolution == 512 else 8
    scene.render.bake.use_clear = True
    bpy.ops.object.bake(type=kind)
    if kind == 'EMIT':
        # glTF roughness uses green, while KHR_materials_specular uses alpha.
        # Pack the two baked scalar parameters into one shared texture.
        values = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
        values[:, 3] = values[:, 0]
        values[:, 0] = 1
        image.pixels.foreach_set(values.ravel())
        image.update()
    extension = 'png' if kind == 'EMIT' else 'webp'
    image.file_format = 'PNG' if kind == 'EMIT' else 'WEBP'
    path = root / f'work/{label}-v26.{extension}'
    quality = 95
    image.save(filepath=str(path), quality=quality)
    if kind != 'EMIT':
        while path.stat().st_size >= 100000 and quality > 65:
            quality -= 5
            image.save(filepath=str(path), quality=quality)
        image.file_format = 'PNG'
        image.save(filepath=str(root / f'work/{label}-v26-reference.png'))
    report[label] = {'bytes': path.stat().st_size, 'resolution': resolution,
                     'quality': quality if kind != 'EMIT' else 'lossless'}
(root / 'work/material26-bake.json').write_text(json.dumps(report, indent=2))
print('BAKE_REPORT', json.dumps(report))
