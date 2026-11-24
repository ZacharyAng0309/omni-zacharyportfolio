from kinematics27 import *
import json

before = asset
after = Asset(root / 'outputs/zachary_character_v27_candidate.glb')
checks = {}
def check(label, condition):
    checks[label] = bool(condition)
    assert condition, label
for field in ['meshes', 'materials', 'images', 'textures', 'samplers', 'skins', 'scenes']:
    check(field + ' preserved', before.g[field] == after.g[field])
bind_accessor = before.g['skins'][0]['inverseBindMatrices']
for index in range(len(before.g['accessors'])):
    if index != bind_accessor:
        check(f'accessor {index} preserved', np.array_equal(before.arr(index), after.arr(index)))
for index, image in enumerate(before.g['images']):
    view = before.g['bufferViews'][image['bufferView']]
    offset = view.get('byteOffset', 0)
    check(f'image {index} bytes preserved', before.bin[offset:offset + view['byteLength']] == after.bin[offset:offset + view['byteLength']])
old_world = world()
new_world = world(node_data=after.g['nodes'])
old_bind = before.arr(bind_accessor).reshape(-1, 4, 4).transpose(0, 2, 1)
new_bind = after.arr(bind_accessor).reshape(-1, 4, 4).transpose(0, 2, 1)
joint_names = [nodes[index]['name'] for index in before.g['skins'][0]['joints']]
old_skin = np.array([old_world[name] @ matrix for name, matrix in zip(joint_names, old_bind)])
new_skin = np.array([new_world[name] @ matrix for name, matrix in zip(joint_names, new_bind)])
errors = {}
for mesh in after.g['meshes'][:6]:
    primitive = mesh['primitives'][0]
    points = after.arr(primitive['attributes']['POSITION'])
    homogeneous = np.column_stack([points, np.ones(len(points))])
    joints = after.arr(primitive['attributes']['JOINTS_0']).astype(int)
    weights = after.arr(primitive['attributes']['WEIGHTS_0'])
    old_surface = np.einsum('nvij,nj,nv->ni', old_skin[joints], homogeneous, weights)
    new_surface = np.einsum('nvij,nj,nv->ni', new_skin[joints], homogeneous, weights)
    maximum = float(np.linalg.norm(old_surface[:, :3] - new_surface[:, :3], axis=1).max() * 1000)
    check(mesh['name'] + ' rest surface within 0.01 mm', maximum < .01)
    check(mesh['name'] + ' normalized weights', np.max(abs(weights.sum(axis=1) - 1)) < 1e-5)
    errors[mesh['name']] = maximum
changed_nodes = [before.g['nodes'][index]['name'] for index in range(len(nodes)) if before.g['nodes'][index] != after.g['nodes'][index]]
expected = {side + suffix for side in ['Left', 'Right'] for suffix in ['ForeArm', 'Hand', 'HandThumb1', 'HandIndex1', 'HandMiddle1', 'HandRing1', 'HandPinky1']}
check('only elbows, wrists and immediate finger attachments changed', set(changed_nodes) == expected)
check('GLB below 3 MB', len(after.raw) < 3000000)
report = {'checks_passed': sum(checks.values()), 'checks_failed': 0, 'glb_bytes': len(after.raw),
          'maximum_rest_surface_error_mm': max(errors.values()), 'mesh_rest_errors_mm': errors,
          'changed_nodes': changed_nodes, 'checks': checks}
(root / 'work/wrist27-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != 'checks'}))
