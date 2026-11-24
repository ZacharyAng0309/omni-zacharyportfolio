"""Relax the hair crown while retaining the authored boundary and GLB data."""
from pathlib import Path
import heapq
import json
import numpy as np
from glb_asset import Asset

root = Path(__file__).resolve().parents[1]
asset = Asset(root / 'outputs/zachary_character_v24_candidate.glb')
primitive = asset.prim('SM_Character_Hair')
positions = asset.arr(primitive['attributes']['POSITION'])
original = positions.copy()
triangles = asset.arr(primitive['indices']).reshape(-1, 3)
unique, inverse = np.unique(np.round(original, 6), axis=0, return_inverse=True)
logical_triangles = inverse[triangles]
edges = np.sort(np.concatenate([logical_triangles[:, [0, 1]],
                                logical_triangles[:, [1, 2]],
                                logical_triangles[:, [2, 0]]]), axis=1)
edges, counts = np.unique(edges, axis=0, return_counts=True)
boundary = np.unique(edges[counts == 1])
neighbors = [[] for _ in unique]
for a, b in edges:
    length = float(np.linalg.norm(unique[a] - unique[b]))
    neighbors[a].append((b, length))
    neighbors[b].append((a, length))
distance = np.full(len(unique), np.inf)
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

def smoothstep(values, start, end):
    weight = np.clip((values - start) / (end - start), 0, 1)
    return weight * weight * (3 - 2 * weight)

weight = smoothstep(distance, .008, .030)
weight *= smoothstep(unique[:, 1], 1.630, 1.665)
face_keys = set(map(tuple, np.round(asset.pos('SM_Character_Face'), 6)))
shared = np.array([tuple(point) in face_keys for point in unique])
weight[shared] = 0
relaxed = unique.copy()
degree = np.bincount(edges.ravel(), minlength=len(unique))
for _ in range(5):
    total = np.zeros_like(relaxed)
    np.add.at(total, edges[:, 0], relaxed[edges[:, 1]])
    np.add.at(total, edges[:, 1], relaxed[edges[:, 0]])
    relaxed += .30 * weight[:, None] * (total / degree[:, None] - relaxed)
delta = relaxed - unique
length = np.linalg.norm(delta, axis=1)
delta *= np.minimum(1, .0022 / np.maximum(length, 1e-12))[:, None]
old_corners = original[triangles]
old_cross = np.cross(old_corners[:, 1] - old_corners[:, 0], old_corners[:, 2] - old_corners[:, 0])
old_area = np.linalg.norm(old_cross, axis=1)
for _ in range(30):
    trial_corners = (original + delta[inverse])[triangles]
    trial_cross = np.cross(trial_corners[:, 1] - trial_corners[:, 0], trial_corners[:, 2] - trial_corners[:, 0])
    area = np.linalg.norm(trial_cross, axis=1)
    bad = (np.sum(old_cross * trial_cross, axis=1) < .1 * old_area * area) | (area < .2 * old_area)
    if not bad.any():
        break
    delta[np.unique(logical_triangles[bad])] *= .5
assert not bad.any(), 'Local relaxation must preserve triangle orientation and area'
positions[:] = original + delta[inverse]

def geometric_normals(points):
    corners = points[triangles]
    face_normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    total = np.zeros_like(unique)
    for corner in range(3):
        np.add.at(total, logical_triangles[:, corner], face_normals)
    total /= np.maximum(np.linalg.norm(total, axis=1)[:, None], 1e-12)
    return total[inverse]

normals = asset.arr(primitive['attributes']['NORMAL'])
old_normals = geometric_normals(original)
new_normals = geometric_normals(positions)
transported = normals + new_normals - old_normals
blend = .5 * weight[inverse, None]
normals[:] = transported * (1 - blend) + new_normals * blend
normals[:] /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
material = asset.g['materials'][primitive['material']]
material['pbrMetallicRoughness']['roughnessFactor'] = .78
material['extensions']['KHR_materials_specular']['specularFactor'] = .18
asset.save(root / 'work/hair25-geometry.glb')
report = {
    'source': 'v24',
    'hair_dimensions_before_m': np.ptp(original, axis=0).tolist(),
    'hair_dimensions_after_m': np.ptp(positions, axis=0).tolist(),
    'max_hair_displacement_mm': float(np.linalg.norm(positions - original, axis=1).max() * 1000),
    'shared_boundary_displacement_mm': float(np.linalg.norm(delta[shared], axis=1).max() * 1000),
    'boundary_vertex_count': int(len(boundary)),
    'affected_hair_vertices': int(np.count_nonzero(np.linalg.norm(positions - original, axis=1) > 1e-7)),
}
(root / 'work/hair25-geometry.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
