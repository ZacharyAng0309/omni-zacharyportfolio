"""Center elbow pivots in the measured sleeve cross-sections."""
from kinematics27 import *
import json

candidate = Asset(root / 'outputs/zachary_character_v27_candidate.glb')
current = world(node_data=candidate.g['nodes'])
sections = json.loads((root / 'work/elbow27-audit.json').read_text())
skin = candidate.g['skins'][0]
matrices = candidate.arr(skin['inverseBindMatrices'])
changes = {}
for side in ['Left', 'Right']:
    name = side + 'ForeArm'
    index = by_name[name]
    section = sections[side]['cross_sections'][0]
    assert section['segments'] > 50 and section['distance_mm'] < 60
    old_world = current[name]
    new_world = old_world.copy()
    new_world[:3, 3] = section['center']
    parent_world = current[nodes[parents[index]]['name']]
    candidate.g['nodes'][index]['translation'] = (np.linalg.inv(parent_world) @ new_world)[:3, 3].tolist()
    for child in candidate.g['nodes'][index].get('children', []):
        child_world = current[nodes[child]['name']]
        candidate.g['nodes'][child]['translation'] = (np.linalg.inv(new_world) @ child_world)[:3, 3].tolist()
    skin_index = skin['joints'].index(index)
    old_bind = matrices[skin_index].reshape(4, 4).T.copy()
    matrices[skin_index] = (np.linalg.inv(new_world) @ old_world @ old_bind).T.reshape(-1)
    changes[name] = {'old_pivot_m': old_world[:3, 3].tolist(), 'new_pivot_m': new_world[:3, 3].tolist(),
                     'offset_corrected_mm': section['distance_mm'], 'cross_section_segments': section['segments']}
candidate.save(root / 'outputs/zachary_character_v27_candidate.glb')
(root / 'work/elbow27-changes.json').write_text(json.dumps(changes, indent=2))
print(json.dumps(changes))
