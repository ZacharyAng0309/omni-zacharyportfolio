"""Validate the exported hair refinement against v24 and texture budgets."""
from pathlib import Path
from copy import deepcopy
import json
import numpy as np
from glb_asset import Asset

root = Path(__file__).resolve().parents[1]
before = Asset(root / 'outputs/zachary_character_v24_candidate.glb')
after = Asset(root / 'outputs/zachary_character_v25_candidate.glb')
checks = {}

def check(label, condition):
    checks[label] = bool(condition)
    assert condition, label

for field in ['nodes', 'skins', 'scenes', 'textures', 'samplers']:
    check(field + ' preserved', before.g.get(field) == after.g.get(field))
expected_meshes = deepcopy(before.g['meshes'])
hair_primitive = next(mesh for mesh in expected_meshes if mesh['name'] == 'SM_Character_Hair')['primitives'][0]
hair_primitive['attributes']['TEXCOORD_1'] = len(before.g['accessors'])
check('mesh definitions preserved with one additional hair UV set', expected_meshes == after.g['meshes'])
hair = after.prim('SM_Character_Hair')
allowed = {hair['attributes']['POSITION'], hair['attributes']['NORMAL']}
for index in range(len(before.g['accessors'])):
    if index not in allowed:
        check(f'accessor {index} preserved', np.array_equal(before.arr(index), after.arr(index)))
for index, material in enumerate(before.g['materials']):
    if index != hair['material']:
        check(f'material {index} preserved', material == after.g['materials'][index])
for mesh in after.g['meshes']:
    for number, primitive in enumerate(mesh['primitives']):
        positions = after.arr(primitive['attributes']['POSITION'])
        normals = after.arr(primitive['attributes']['NORMAL'])
        indices = after.arr(primitive['indices'])
        label = mesh['name'] + f' primitive {number}'
        check(label + ' valid geometry', np.isfinite(positions).all() and indices.max() < len(positions))
        check(label + ' unit normals', np.max(abs(np.linalg.norm(normals, axis=1) - 1)) < .002)

def image_bytes(asset, index):
    view = asset.g['bufferViews'][asset.g['images'][index]['bufferView']]
    offset = view.get('byteOffset', 0)
    return asset.bin[offset:offset + view['byteLength']]

check('original body and face texture preserved', image_bytes(before, 0) == image_bytes(after, 0))
sizes = [len(image_bytes(after, index)) for index in range(len(after.g['images']))]
check('new hair textures below 100 KB', max(sizes[1:]) < 100000)
check('GLB below 3 MB', len(after.raw) < 3000000)
old_points = before.pos('SM_Character_Hair')
new_points = after.pos('SM_Character_Hair')
triangles = after.arr(hair['indices']).reshape(-1, 3)
old_triangles, new_triangles = old_points[triangles], new_points[triangles]
old_cross = np.cross(old_triangles[:, 1] - old_triangles[:, 0], old_triangles[:, 2] - old_triangles[:, 0])
new_cross = np.cross(new_triangles[:, 1] - new_triangles[:, 0], new_triangles[:, 2] - new_triangles[:, 0])
flipped = int(np.count_nonzero(np.sum(old_cross * new_cross, axis=1) < 0))
check('zero hair triangles reversed relative to v24', flipped == 0)
old_uv = after.arr(hair['attributes']['TEXCOORD_0'])
new_uv = after.arr(hair['attributes']['TEXCOORD_1'])
check('packed UVs finite and inside texture', np.isfinite(new_uv).all() and new_uv.min() >= 0 and new_uv.max() <= 1)
old_edges = old_uv[triangles[:, 1:]] - old_uv[triangles[:, :1]]
new_edges = new_uv[triangles[:, 1:]] - new_uv[triangles[:, :1]]
scale = json.loads((root / 'work/hair25-uv-report.json').read_text())['uv_linear_scale']
check('UV repacking preserves every triangle shape', np.max(abs(new_edges - old_edges * scale)) < 1e-6)
check('hair color uses packed UVs', after.g['materials'][1]['pbrMetallicRoughness']['baseColorTexture']['texCoord'] == 1)
check('hair normals use packed UVs', after.g['materials'][1]['normalTexture']['texCoord'] == 1)
report = {'checks_passed': sum(checks.values()), 'checks_failed': 0,
          'glb_bytes': len(after.raw), 'texture_bytes': sizes,
          'existing_texture_budget_excess_bytes': max(0, sizes[0] - 100000),
          'triangles': sum(after.g['accessors'][p['indices']]['count'] // 3 for mesh in after.g['meshes'] for p in mesh['primitives']),
          'reversed_hair_triangles': flipped,
          'maximum_hair_displacement_mm': float(np.linalg.norm(new_points - old_points, axis=1).max() * 1000),
          'checks': checks}
(root / 'work/hair25-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != 'checks'}))
