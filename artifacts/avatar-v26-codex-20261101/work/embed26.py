from pathlib import Path
from glb_asset import Asset

root = Path(__file__).resolve().parents[1]
asset = Asset(root / 'outputs/zachary_character_v25_candidate.glb')
replacement = {}
for index, label in [(0, 'body-albedo'), (1, 'hair-albedo')]:
    image = asset.g['images'][index]
    image['name'] = 'T_v26_' + label
    replacement[image['bufferView']] = (root / f'work/{label}-v26.webp').read_bytes()
binary = bytearray()
for index, view in enumerate(asset.g['bufferViews']):
    offset = view.get('byteOffset', 0)
    data = replacement.get(index, asset.bin[offset:offset + view['byteLength']])
    binary.extend(b'\0' * ((-len(binary)) % 4))
    view['byteOffset'] = len(binary)
    view['byteLength'] = len(data)
    binary.extend(data)
texture_indices = {}
for label in ['body-roughness', 'hair-roughness']:
    data = (root / f'work/{label}-v26.png').read_bytes()
    binary.extend(b'\0' * ((-len(binary)) % 4))
    view_index = len(asset.g['bufferViews'])
    asset.g['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    image_index = len(asset.g['images'])
    asset.g['images'].append({'bufferView': view_index, 'mimeType': 'image/png', 'name': 'T_v26_' + label})
    texture_indices[label] = len(asset.g['textures'])
    asset.g['textures'].append({'source': image_index, 'sampler': 0})
for index, material in enumerate(asset.g['materials'][:6]):
    pbr = material['pbrMetallicRoughness']
    pbr['baseColorFactor'] = [1, 1, 1, 1]
    pbr['roughnessFactor'] = 1
    pbr['metallicRoughnessTexture'] = {
        'index': texture_indices['hair-roughness' if index == 1 else 'body-roughness'],
        'texCoord': 1 if index == 1 else 0,
    }
    material['extensions']['KHR_materials_specular'] = {
        'specularFactor': 1,
        'specularTexture': dict(pbr['metallicRoughnessTexture']),
    }
binary.extend(b'\0' * ((-len(binary)) % 4))
asset.bin = binary
asset.g['buffers'][0]['byteLength'] = len(binary)
asset.save(root / 'outputs/zachary_character_v26_candidate.glb')
print('GLB bytes', (root / 'outputs/zachary_character_v26_candidate.glb').stat().st_size)
