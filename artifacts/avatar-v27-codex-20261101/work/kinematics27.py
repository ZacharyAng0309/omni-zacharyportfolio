"""glTF forward kinematics with Three.js XYZ Euler target conventions."""
from pathlib import Path
import re
import math
import numpy as np
from glb_asset import Asset

root = Path(__file__).resolve().parents[1]
asset = Asset(root / 'outputs/zachary_character_v26_candidate.glb')
nodes = asset.g['nodes']
by_name = {node.get('name'): index for index, node in enumerate(nodes)}
parents = {child: index for index, node in enumerate(nodes) for child in node.get('children', [])}

def rotation_quaternion(values):
    x, y, z, w = values
    return np.array([[1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
                     [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
                     [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)]])

def rotation_xyz(values):
    x, y, z = values
    cx, cy, cz = np.cos(values)
    sx, sy, sz = np.sin(values)
    return np.array([[cy*cz, -cy*sz, sy],
                     [cx*sz + sx*sy*cz, cx*cz - sx*sy*sz, -sx*cy],
                     [sx*sz - cx*sy*cz, sx*cz + cx*sy*sz, cx*cy]])

def euler_xyz(matrix):
    y = math.asin(np.clip(matrix[0, 2], -1, 1))
    if abs(matrix[0, 2]) < .9999999:
        return np.array([math.atan2(-matrix[1, 2], matrix[2, 2]), y, math.atan2(-matrix[0, 1], matrix[0, 0])])
    return np.array([math.atan2(matrix[2, 1], matrix[1, 1]), y, 0])

def world(overrides=None, node_data=nodes):
    overrides = overrides or {}
    result = {}
    def visit(index):
        if index in result:
            return result[index]
        node = node_data[index]
        local = np.eye(4)
        local[:3, 3] = node.get('translation', [0, 0, 0])
        rotation = rotation_xyz(overrides[node['name']]) if node.get('name') in overrides else rotation_quaternion(node.get('rotation', [0, 0, 0, 1]))
        local[:3, :3] = rotation @ np.diag(node.get('scale', [1, 1, 1]))
        if 'matrix' in node:
            local = np.array(node['matrix']).reshape(4, 4).T
        result[index] = visit(parents[index]) @ local if index in parents else local
        return result[index]
    for index in range(len(node_data)):
        visit(index)
    return {name: result[index] for name, index in by_name.items()}

rest = world()
if __name__ == '__main__':
    for side in ['Right', 'Left']:
        for suffix in ['Arm', 'ForeArm', 'Hand', 'HandIndex1', 'HandIndex3', 'HandMiddle3', 'HandPinky3', 'HandThumb3']:
            name = side + suffix
            print(name, np.round(rest[name][:3, 3], 4))
