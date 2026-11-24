"""Build and review a local, part-guided procedural hair material."""
import bpy
import heapq
import numpy as np
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
scene = bpy.data.scenes['Portrait review v25']
bpy.context.window.scene = scene
hair = next(obj for obj in scene.objects if obj.name.startswith('SM_Character_Hair'))
points = np.array([vertex.co[:] for vertex in hair.data.vertices])
logical, inverse = np.unique(np.round(points, 6), axis=0, return_inverse=True)
triangles = np.array([polygon.vertices[:] for polygon in hair.data.polygons])
edges = np.sort(inverse[np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])], axis=1)
edges, counts = np.unique(edges, axis=0, return_counts=True)
boundary = np.unique(edges[counts == 1])
neighbors = [[] for _ in logical]
for a, b in edges:
    length = float(np.linalg.norm(logical[a] - logical[b]))
    neighbors[a].append((b, length))
    neighbors[b].append((a, length))
distance = np.full(len(logical), np.inf)
distance[boundary] = 0
queue = [(0, int(index)) for index in boundary]
heapq.heapify(queue)
while queue:
    current, index = heapq.heappop(queue)
    if current > distance[index]:
        continue
    for other, length in neighbors[index]:
        candidate = current + length
        if candidate < distance[other]:
            distance[other] = candidate
            heapq.heappush(queue, (candidate, int(other)))
weight = np.clip(distance[inverse] / .045, 0, 1)
weight = weight * weight * (3 - 2 * weight)
attribute = hair.data.attributes.new('hair_surface_weight', 'FLOAT', 'POINT')
attribute.data.foreach_set('value', weight.astype(np.float32))

material = hair.data.materials[0]
material.name = 'M_Hair_v25_Combed'
tree = material.node_tree
nodes, links = tree.nodes, tree.links
shader = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
original = shader.inputs['Base Color'].links[0].from_socket
for link in list(shader.inputs['Normal'].links):
    links.remove(link)
position = nodes.new('ShaderNodeNewGeometry')
separate = nodes.new('ShaderNodeSeparateXYZ')
links.new(position.outputs['Position'], separate.inputs[0])

def math_node(operation, first, second):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for socket, value in zip(node.inputs[:2], (first, second)):
        if isinstance(value, (float, int)):
            socket.default_value = value
        else:
            links.new(value, socket)
    return node.outputs[0]

# Longitude about the part makes strands descend around the scalp on every side.
across = math_node('ADD', separate.outputs['X'], .014)
forward = math_node('SUBTRACT', .015, separate.outputs['Y'])
angle = math_node('ARCTAN2', across, forward)
flow = nodes.new('ShaderNodeCombineXYZ')
links.new(math_node('MULTIPLY', math_node('SINE', angle, 0), 65), flow.inputs['X'])
links.new(math_node('MULTIPLY', math_node('COSINE', angle, 0), 65), flow.inputs['Y'])
links.new(math_node('MULTIPLY', separate.outputs['Z'], 18), flow.inputs['Z'])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1
noise.inputs['Detail'].default_value = 2
noise.inputs['Roughness'].default_value = .65
links.new(flow.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .22
ramp.color_ramp.elements[0].color = (.014, .009, .006, 1)
ramp.color_ramp.elements[1].position = .78
ramp.color_ramp.elements[1].color = (.028, .017, .011, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
mask = nodes.new('ShaderNodeAttribute')
mask.attribute_name = 'hair_surface_weight'
mix = nodes.new('ShaderNodeMixRGB')
mix.blend_type = 'MIX'
links.new(math_node('MULTIPLY', mask.outputs['Fac'], .82), mix.inputs[0])
links.new(original, mix.inputs[1])
links.new(ramp.outputs['Color'], mix.inputs[2])
links.new(mix.outputs[0], shader.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Distance'].default_value = .00012
links.new(math_node('MULTIPLY', mask.outputs['Fac'], .4), bump.inputs['Strength'])
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs['Normal'], shader.inputs['Normal'])
shader.inputs['Roughness'].default_value = .66
shader.inputs['Specular IOR Level'].default_value = .09
scene.cycles.samples = 48
for label, location in [('front', (0, -3, 1.585)), ('quarter', (1.45, -2.62, 1.585)), ('left', (-2.9, -.5, 1.585))]:
    scene.camera.location = location
    scene.camera.rotation_euler = (Vector((0, 0, 1.585)) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(root / f'work/hair25-surface-{label}.png')
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root / 'work/hair25-surface.blend'), compress=True)
