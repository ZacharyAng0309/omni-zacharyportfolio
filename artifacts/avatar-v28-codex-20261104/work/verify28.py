from kinematics27 import *
import json

before = Asset(root / 'outputs/zachary_character_v27_candidate.glb')
after = Asset(root / 'outputs/zachary_character_v28_candidate.glb')
checks = {}
def check(label, condition):
    checks[label] = bool(condition)
    assert condition, label
for field in ['meshes', 'materials', 'images', 'textures', 'samplers', 'skins', 'scenes']:
    check(field + ' preserved', before.g[field] == after.g[field])
bind_accessor = before.g['skins'][0]['inverseBindMatrices']
hand_attributes = before.prim('SM_Character_Hands')['attributes']
weight_accessors = {hand_attributes['JOINTS_0'], hand_attributes['WEIGHTS_0']}
for index in range(len(before.g['accessors'])):
    if index != bind_accessor and index not in weight_accessors:
        check(f'accessor {index} preserved', np.array_equal(before.arr(index), after.arr(index)))
for index, image in enumerate(before.g['images']):
    view = before.g['bufferViews'][image['bufferView']]
    offset = view.get('byteOffset', 0)
    check(f'image {index} bytes preserved', before.bin[offset:offset + view['byteLength']] == after.bin[offset:offset + view['byteLength']])
old_world = world(node_data=before.g['nodes'])
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
hand_points = before.pos('SM_Character_Hands')
hoodie_keys = set(map(tuple, np.round(before.pos('SM_Cloth_Hoodie'), 6)))
seam_indices = [i for i, point in enumerate(hand_points) if tuple(np.round(point, 6)) in hoodie_keys]
for semantic in ['JOINTS_0', 'WEIGHTS_0']:
    accessor = hand_attributes[semantic]
    check('cuff seam ' + semantic + ' preserved', np.array_equal(before.arr(accessor)[seam_indices], after.arr(accessor)[seam_indices]))
check('four hand influences maximum', after.arr(hand_attributes['WEIGHTS_0']).shape[1] == 4)
check('hand weights nonnegative', np.min(after.arr(hand_attributes['WEIGHTS_0'])) >= 0)
changed_nodes = [before.g['nodes'][index]['name'] for index in range(len(nodes)) if before.g['nodes'][index] != after.g['nodes'][index]]
expected = {side + 'Hand' + finger + str(number) for side in ['Left','Right'] for finger in ['Thumb','Index','Middle','Ring','Pinky'] for number in [1,2,3]}
check('only thirty finger joints changed', set(changed_nodes) == expected)
check('GLB below 3 MB', len(after.raw) < 3000000)
report = {'checks_passed': sum(checks.values()), 'checks_failed': 0, 'glb_bytes': len(after.raw),
          'maximum_rest_surface_error_mm': max(errors.values()), 'mesh_rest_errors_mm': errors,
          'changed_nodes': changed_nodes, 'checks': checks}
(root / 'work/finger28-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != 'checks'}))
