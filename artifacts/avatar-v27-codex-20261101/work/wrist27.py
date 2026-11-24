"""Align wrist pivots to the hand/garment seams without changing the rest surface."""
from kinematics27 import *
import json

candidate = Asset(root / 'outputs/zachary_character_v26_candidate.glb')
primitive = candidate.prim('SM_Character_Hands')
points = candidate.pos('SM_Character_Hands')
triangles = candidate.arr(primitive['indices']).reshape(-1, 3)
unique, inverse = np.unique(np.round(points, 6), axis=0, return_inverse=True)
parent = list(range(len(unique)))
def representative(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index
for a, b, c in inverse[triangles]:
    parent[representative(b)] = representative(a)
    parent[representative(c)] = representative(a)
groups = {}
for index in range(len(unique)):
    groups.setdefault(representative(index), []).append(index)
hoodie_keys = set(map(tuple, np.round(candidate.pos('SM_Cloth_Hoodie'), 6)))
skin = candidate.g['skins'][0]
matrices = candidate.arr(skin['inverseBindMatrices'])
changes = {}
for indices in groups.values():
    seam = np.array([unique[index] for index in indices if tuple(unique[index]) in hoodie_keys])
    if len(seam) < 20:
        continue
    center = seam.mean(axis=0)
    name = 'LeftHand' if center[0] > 0 else 'RightHand'
    node_index = by_name[name]
    old_world = rest[name]
    new_world = old_world.copy()
    new_world[:3, 3] = center
    parent_world = rest[nodes[parents[node_index]]['name']]
    candidate.g['nodes'][node_index]['translation'] = (np.linalg.inv(parent_world) @ new_world)[:3, 3].tolist()
    for child in nodes[node_index].get('children', []):
        child_world = rest[nodes[child]['name']]
        candidate.g['nodes'][child]['translation'] = (np.linalg.inv(new_world) @ child_world)[:3, 3].tolist()
    skin_index = skin['joints'].index(node_index)
    old_bind = matrices[skin_index].reshape(4, 4).T.copy()
    matrices[skin_index] = (np.linalg.inv(new_world) @ old_world @ old_bind).T.reshape(-1)
    changes[name] = {'seam_vertices': len(seam), 'old_pivot_m': old_world[:3, 3].tolist(),
                     'new_pivot_m': center.tolist(), 'offset_corrected_mm': float(np.linalg.norm(center - old_world[:3, 3]) * 1000)}
assert len(changes) == 2
candidate.save(root / 'outputs/zachary_character_v27_candidate.glb')
(root / 'work/wrist27-changes.json').write_text(json.dumps(changes, indent=2))
print(json.dumps(changes))
