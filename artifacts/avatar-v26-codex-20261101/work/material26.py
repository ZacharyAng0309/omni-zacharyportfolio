"""Repair skin/clothing color transitions using texture content and UV seams."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
scene = bpy.data.scenes['Portrait review v25']
scene.name = 'Portrait review v26'
bpy.context.window.scene = scene
face = next(obj for obj in scene.objects if obj.name.startswith('SM_Character_Face'))
hair = next(obj for obj in scene.objects if obj.name.startswith('SM_Character_Hair'))
hoodie = next(obj for obj in scene.objects if obj.name.startswith('SM_Cloth_Hoodie'))
source_image = next(node.image for node in face.data.materials[0].node_tree.nodes if node.type == 'TEX_IMAGE')
pixels = np.array(source_image.pixels[:]).reshape(source_image.size[1], source_image.size[0], 4)

# Identify the isolated cowl patch from its UV component, cool fabric color,
# and shared garment boundary. No anatomical coordinate threshold is used.
triangles = np.array([poly.vertices[:] for poly in hair.data.polygons])
parent = list(range(len(hair.data.vertices)))
def representative(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index
for a, b, c in triangles:
    parent[representative(b)] = representative(a)
    parent[representative(c)] = representative(a)
groups = {}
for index in range(len(parent)):
    groups.setdefault(representative(index), []).append(index)
vertex_uv = np.zeros((len(parent), 2))
for loop in hair.data.loops:
    vertex_uv[loop.vertex_index] = hair.data.uv_layers[0].data[loop.index].uv[:]
width, height = source_image.size
sampled = pixels[np.clip((vertex_uv[:, 1] * height).astype(int), 0, height - 1),
                 np.clip((vertex_uv[:, 0] * width).astype(int), 0, width - 1), :3]
hoodie_keys = {tuple(round(value, 6) for value in vertex.co) for vertex in hoodie.data.vertices}
cloth_weight = np.zeros(len(parent), dtype=np.float32)
cloth_components = []
for indices in groups.values():
    color = np.median(sampled[indices], axis=0)
    shared = sum(tuple(round(value, 6) for value in hair.data.vertices[index].co) in hoodie_keys for index in indices)
    if color[2] > color[0] * 1.05 and shared > 0:
        cloth_weight[indices] = 1
        cloth_components.append({'vertices': len(indices), 'shared_garment_vertices': shared})
assert cloth_components, 'Expected a fabric UV component adjoining the hoodie'
attribute = hair.data.attributes.new('cowl_material_region', 'FLOAT', 'POINT')
attribute.data.foreach_set('value', cloth_weight)

def scalar(tree, operation, first, second=0):
    node = tree.nodes.new('ShaderNodeMath')
    node.operation = operation
    for socket, value in zip(node.inputs[:2], (first, second)):
        if isinstance(value, (float, int)):
            socket.default_value = value
        else:
            tree.links.new(value, socket)
    return node.outputs[0]

def ramp(tree, value, low, high):
    node = tree.nodes.new('ShaderNodeMapRange')
    node.interpolation_type = 'SMOOTHSTEP'
    node.clamp = True
    node.inputs['From Min'].default_value = low
    node.inputs['From Max'].default_value = high
    tree.links.new(value, node.inputs['Value'])
    return node.outputs['Result']

def body_color(tree, uv_name):
    uv = tree.nodes.new('ShaderNodeUVMap')
    uv.uv_map = uv_name
    texture = tree.nodes.new('ShaderNodeTexImage')
    texture.image = source_image
    tree.links.new(uv.outputs[0], texture.inputs['Vector'])
    channels = tree.nodes.new('ShaderNodeSeparateColor')
    channels.mode = 'RGB'
    tree.links.new(texture.outputs['Color'], channels.inputs[0])
    red, blue = channels.outputs['Red'], channels.outputs['Blue']
    warm = ramp(tree, scalar(tree, 'SUBTRACT', red, blue), .025, .08)
    bright_skin = ramp(tree, red, .14, .30)
    neutral_highlights = ramp(tree, red, .40, .65)
    skin = scalar(tree, 'MAXIMUM', scalar(tree, 'MULTIPLY', warm, bright_skin), neutral_highlights)
    tint = tree.nodes.new('ShaderNodeMixRGB')
    tint.inputs[1].default_value = (.75, .75, .77, 1)
    tint.inputs[2].default_value = (.86, .83, .81, 1)
    tree.links.new(skin, tint.inputs[0])
    color = tree.nodes.new('ShaderNodeMixRGB')
    color.blend_type = 'MULTIPLY'
    color.inputs[0].default_value = 1
    tree.links.new(texture.outputs['Color'], color.inputs[1])
    tree.links.new(tint.outputs[0], color.inputs[2])
    roughness = scalar(tree, 'SUBTRACT', .92, scalar(tree, 'MULTIPLY', skin, .30))
    specular = scalar(tree, 'ADD', .12, scalar(tree, 'MULTIPLY', skin, .16))
    return color.outputs[0], skin, roughness, specular

for obj in [obj for obj in scene.objects if obj.type == 'MESH' and obj.name.startswith(('SM_Character_', 'SM_Cloth_'))]:
    material = obj.data.materials[0].copy()
    material.name = 'M_v26_' + obj.name.split('.')[0]
    obj.data.materials[0] = material
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    current = shader.inputs['Base Color'].links[0].from_socket
    color, skin, roughness, specular = body_color(tree, obj.data.uv_layers[0].name)
    if obj == hair:
        cloth = tree.nodes.new('ShaderNodeAttribute')
        cloth.attribute_name = 'cowl_material_region'
        repair = scalar(tree, 'MAXIMUM', skin, cloth.outputs['Fac'])
        blend = tree.nodes.new('ShaderNodeMixRGB')
        tree.links.new(repair, blend.inputs[0])
        tree.links.new(current, blend.inputs[1])
        tree.links.new(color, blend.inputs[2])
        color = blend.outputs[0]
        roughness = scalar(tree, 'ADD', scalar(tree, 'MULTIPLY', scalar(tree, 'SUBTRACT', 1, repair), .66),
                           scalar(tree, 'MULTIPLY', repair, roughness))
        specular = scalar(tree, 'ADD', scalar(tree, 'MULTIPLY', scalar(tree, 'SUBTRACT', 1, repair), .18),
                          scalar(tree, 'MULTIPLY', repair, specular))
    tree.links.new(color, shader.inputs['Base Color'])
    tree.links.new(roughness, shader.inputs['Roughness'])
    tree.links.new(scalar(tree, 'MULTIPLY', specular, .5), shader.inputs['Specular IOR Level'])
    # Retain these sockets for deterministic bake selection.
    color.node.label = 'V26_FINAL_COLOR'
    roughness.node.label = 'V26_FINAL_ROUGHNESS'
    specular.node.label = 'V26_FINAL_SPECULAR'

scene.cycles.samples = 32
for label, location in [('front', (0, -3, 1.585)), ('left', (-2.9, -.5, 1.585)), ('right', (2.9, -.5, 1.585))]:
    scene.camera.location = location
    scene.camera.rotation_euler = (Vector((0, 0, 1.585)) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(root / f'work/material26-{label}.png')
    bpy.ops.render.render(write_still=True)
(root / 'work/material26-regions.json').write_text(json.dumps({'cowl_components': cloth_components}, indent=2))
print('IMAGE_SAVE_PARAMETERS', list(bpy.types.Image.bl_rna.functions['save'].parameters.keys()))
bpy.ops.wm.save_as_mainfile(filepath=str(root / 'work/material26.blend'), compress=True)
