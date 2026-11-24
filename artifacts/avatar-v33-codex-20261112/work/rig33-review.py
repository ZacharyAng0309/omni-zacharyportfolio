"""Render portfolio gesture targets using their glTF joint transforms."""
import bpy
import json
import math
import re
import sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_asset import Asset

root = Path(__file__).resolve().parents[1]
asset = Asset(root / 'outputs/zachary_character_v33_candidate.glb')
scene = bpy.data.scenes['Whole model review v33']
bpy.context.window.scene = scene
rig = next(obj for obj in scene.objects if obj.type == 'ARMATURE')
source = Path(r'D:\omni-workstation\projects\ZacharyPortfolio\src\graphics\SceneController.ts').read_text(encoding='utf-8')
def numbers(block):
    return {key: float(value) for key, value in re.findall(r'(\w+)\s*:\s*(-?\d+(?:\.\d+)?)', block)}
station = next(numbers(block) for block in re.findall(r'gltf:\s*\{([^}]+)\}', source) if 'rightArmX' in numbers(block))
poses = {'station-1': station}
for name in ['glasses_adjust', 'inspect_tablet', 'keynote_present']:
    poses[name] = {**station, **numbers(re.search(name + r':\s*\{([^}]+)\}', source).group(1))}
fitted = json.loads((root / 'work/poses27.json').read_text())
for name, values in fitted.items():
    poses[name] = {**station, **values}
nodes = asset.g['nodes']
children = {child for node in nodes for child in node.get('children', [])}
roots = [index for index in range(len(nodes)) if index not in children]
conversion = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
def three_euler(quaternion):
    matrix = quaternion.to_matrix()
    y = math.asin(max(-1, min(1, matrix[0][2])))
    if abs(matrix[0][2]) < .9999999:
        return [math.atan2(-matrix[1][2], matrix[2][2]), y, math.atan2(-matrix[0][1], matrix[0][0])]
    return [math.atan2(matrix[2][1], matrix[1][1]), y, 0]

def world_matrices(parameters):
    result = {}
    def visit(index, parent):
        node = nodes[index]
        x, y, z, w = node.get('rotation', [0, 0, 0, 1])
        rotation = Quaternion((w, x, y, z))
        name = node.get('name', '')
        prefix = {'LeftArm': 'leftArm', 'RightArm': 'rightArm',
                  'LeftForeArm': 'leftFore', 'RightForeArm': 'rightFore',
                  'LeftHand': 'leftHand', 'RightHand': 'rightHand'}.get(name)
        euler = three_euler(rotation)
        changed = False
        if prefix:
            for axis, suffix in enumerate('XYZ'):
                if prefix + suffix in parameters:
                    euler[axis] = parameters[prefix + suffix]
                    changed = True
        if re.fullmatch(r'(Left|Right)Hand(Thumb|Index|Middle|Ring|Pinky)[123]', name) and parameters:
            curl = parameters.get('fingerCurl', .10) * (.55 if 'Thumb' in name else 1)
            rotation = rotation @ Quaternion((1, 0, 0), curl)
        if changed:
            rotation = Quaternion((1, 0, 0), euler[0]) @ Quaternion((0, 1, 0), euler[1]) @ Quaternion((0, 0, 1), euler[2])
        local = Matrix.LocRotScale(Vector(node.get('translation', [0, 0, 0])), rotation, Vector(node.get('scale', [1, 1, 1])))
        if 'matrix' in node:
            local = Matrix(np.array(node['matrix']).reshape(4, 4).T.tolist())
        result[index] = parent @ local
        for child in node.get('children', []):
            visit(child, result[index])
    for index in roots:
        visit(index, Matrix.Identity(4))
    return result

rest = world_matrices({})
joint_by_name = {node.get('name'): index for index, node in enumerate(nodes)}
armature_world = rig.matrix_world.copy()
report = {}
skin = asset.g['skins'][0]
inverse_bind = asset.arr(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
for pose_index, (label, parameters) in enumerate(poses.items()):
    frame = 1 + pose_index * 40
    scene.frame_set(frame)
    posed = world_matrices(parameters)
    desired = {}
    for bone in rig.data.bones:
        index = joint_by_name[bone.name]
        world_delta = conversion @ posed[index] @ rest[index].inverted() @ conversion.inverted()
        desired[bone.name] = armature_world.inverted() @ world_delta @ armature_world @ bone.matrix_local
    for bone in rig.data.bones:
        basis = bone.matrix_local.inverted() @ desired[bone.name]
        if bone.parent:
            basis = bone.matrix_local.inverted() @ bone.parent.matrix_local @ desired[bone.parent.name].inverted() @ desired[bone.name]
        pose_bone = rig.pose.bones[bone.name]
        pose_bone.rotation_mode = 'QUATERNION'
        pose_bone.matrix_basis = basis
        for property_name in ['location', 'rotation_quaternion', 'scale']:
            pose_bone.keyframe_insert(data_path=property_name, frame=frame, group=bone.name)
    bpy.context.view_layer.update()
    scene.timeline_markers.new(label, frame=frame)
    errors = []
    for mesh_name in ['SM_Character_Hands', 'SM_Cloth_Hoodie']:
        obj = next(obj for obj in scene.objects if obj.name.startswith(mesh_name))
        lookup = {tuple(round(value, 5) for value in vertex.co): vertex.index for vertex in obj.data.vertices}
        primitive = asset.prim(mesh_name)
        points = asset.arr(primitive['attributes']['POSITION'])
        joints = asset.arr(primitive['attributes']['JOINTS_0'])
        weights = asset.arr(primitive['attributes']['WEIGHTS_0'])
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        for index in range(0, len(points), max(1, len(points) // 100)):
            point = Vector((*points[index], 1))
            key = tuple(round(value, 5) for value in (conversion @ point)[:3])
            if key not in lookup:
                continue
            expected = Vector((0, 0, 0, 0))
            for joint, weight in zip(joints[index], weights[index]):
                expected += (posed[skin['joints'][int(joint)]] @ Matrix(inverse_bind[int(joint)].tolist()) @ point) * float(weight)
            expected = (conversion @ expected).to_3d()
            actual = evaluated.matrix_world @ mesh.vertices[lookup[key]].co
            errors.append((expected - actual).length)
        evaluated.to_mesh_clear()
    assert errors and max(errors) < .0001, (label, max(errors, default=-1))
    report[label] = {'sampled_vertices': len(errors), 'maximum_skinning_difference_mm': max(errors) * 1000,
                     'finger_curl_radians': parameters.get('fingerCurl', .10)}
    scene.cycles.samples = 24
    scene.render.filepath = str(root / f'work/rig33-{label}.png')
    # Numeric gesture verification retained; unchanged body poses need no repeated renders.
(root / 'work/rig33-review.json').write_text(json.dumps(report, indent=2))
print('GESTURE_VALIDATION', json.dumps(report))
scene.frame_start = 1
scene.frame_end = 121
scene.frame_set(1)
scene.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=str(root / 'outputs/Zachary_Avatar_v33_Review.blend'), compress=True)

