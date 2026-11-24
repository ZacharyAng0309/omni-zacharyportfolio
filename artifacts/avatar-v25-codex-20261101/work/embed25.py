"""Embed the baked hair maps and additional UVs into the verified GLB structure."""
from pathlib import Path
import numpy as np
from glb_asset import Asset

root = Path(__file__).resolve().parents[1]
asset = Asset(root / 'work/hair25-geometry.glb')
primitive = asset.prim('SM_Character_Hair')
material = asset.g['materials'][primitive['material']]
material['name'] = 'M_Hair_v25_Combed'
material['pbrMetallicRoughness']['roughnessFactor'] = .66
material['extensions']['KHR_materials_specular']['specularFactor'] = .18
material['pbrMetallicRoughness']['baseColorTexture']['texCoord'] = 1
material['normalTexture']['texCoord'] = 1
replacements = {}
for image_index, label, extension in [(1, 'albedo', 'webp'), (2, 'normal', 'png')]:
    image = asset.g['images'][image_index]
    image['name'] = 'T_Hair_v25_' + label
    replacements[image['bufferView']] = (root / f'work/hair25-{label}.{extension}').read_bytes()
binary = bytearray()
for index, view in enumerate(asset.g['bufferViews']):
    start = view.get('byteOffset', 0)
    data = replacements.get(index, asset.bin[start:start + view['byteLength']])
    binary.extend(b'\x00' * ((-len(binary)) % 4))
    view['byteOffset'] = len(binary)
    view['byteLength'] = len(data)
    binary.extend(data)
binary.extend(b'\x00' * ((-len(binary)) % 4))
uv = np.load(root / 'work/hair25-uv.npy').astype('<f4')
view_index = len(asset.g['bufferViews'])
asset.g['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary),
                             'byteLength': uv.nbytes, 'target': 34962})
binary.extend(uv.tobytes())
primitive['attributes']['TEXCOORD_1'] = len(asset.g['accessors'])
asset.g['accessors'].append({'bufferView': view_index, 'componentType': 5126,
                            'count': len(uv), 'type': 'VEC2',
                            'min': uv.min(axis=0).tolist(), 'max': uv.max(axis=0).tolist()})
asset.bin = binary
asset.g['buffers'][0]['byteLength'] = len(binary)
path = root / 'outputs/zachary_character_v25_candidate.glb'
asset.save(path)
print('GLB bytes', path.stat().st_size)
