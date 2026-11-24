"""Repack existing UV islands into a second, hair-only coordinate set."""
from pathlib import Path
import json
import numpy as np
from glb_asset import Asset

root = Path(__file__).resolve().parents[1]
asset = Asset(root / 'work/hair25-geometry.glb')
primitive = asset.prim('SM_Character_Hair')
uv = asset.arr(primitive['attributes']['TEXCOORD_0'])
triangles = asset.arr(primitive['indices']).reshape(-1, 3)
parent = list(range(len(uv)))

def representative(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index

for a, b, c in triangles:
    parent[representative(b)] = representative(a)
    parent[representative(c)] = representative(a)
groups = {}
for index in range(len(uv)):
    groups.setdefault(representative(index), []).append(index)
charts = sorted(groups.values(), key=lambda indices: np.ptp(uv[indices], axis=0)[1], reverse=True)
padding = 8 / 1024

def shelf_layout(scale):
    placements = []
    x, y, height = 0, 0, 0
    for indices in charts:
        width, depth = np.ptp(uv[indices], axis=0) * scale + 2 * padding
        if x + width > 1:
            x = 0
            y += height
            height = 0
        if y + depth > 1 or width > 1:
            return None
        placements.append((x + padding, y + padding))
        x += width
        height = max(height, depth)
    return placements

low, high = 0, 10
for _ in range(40):
    middle = (low + high) / 2
    if shelf_layout(middle) is None:
        high = middle
    else:
        low = middle
scale = low * .999
packed = np.empty_like(uv)
placements = shelf_layout(scale)
for indices, offset in zip(charts, placements):
    packed[indices] = (uv[indices] - uv[indices].min(axis=0)) * scale + offset
np.save(root / 'work/hair25-uv.npy', packed)
rows = []
for point, old, new in zip(asset.pos('SM_Character_Hair'), uv, packed):
    rows.append({'position': [float(point[0]), float(-point[2]), float(point[1])],
                 'old_uv': [float(old[0]), float(1 - old[1])],
                 'new_uv': [float(new[0]), float(1 - new[1])]})
(root / 'work/hair25-uv.json').write_text(json.dumps(rows))
report = {'islands': len(charts), 'uv_linear_scale': scale,
          'padding_pixels_at_1024': 8, 'original_coordinates_preserved': True}
(root / 'work/hair25-uv-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
