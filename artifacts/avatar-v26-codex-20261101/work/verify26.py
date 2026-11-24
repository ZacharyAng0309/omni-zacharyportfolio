from pathlib import Path
from io import BytesIO
import json
import numpy as np
from PIL import Image, ImageDraw
from glb_asset import Asset

root = Path(__file__).resolve().parents[1]
before = Asset(root / 'outputs/zachary_character_v25_candidate.glb')
after = Asset(root / 'outputs/zachary_character_v26_candidate.glb')
checks = {}
def check(label, condition):
    checks[label] = bool(condition)
    assert condition, label

for field in ['nodes', 'skins', 'meshes', 'scenes', 'accessors', 'samplers']:
    check(field + ' preserved', before.g[field] == after.g[field])
for index in range(len(before.g['accessors'])):
    check(f'accessor {index} byte values preserved', np.array_equal(before.arr(index), after.arr(index)))
for index in range(6, len(before.g['materials'])):
    check(f'glasses material {index} preserved', before.g['materials'][index] == after.g['materials'][index])
check('hair normal routing preserved', before.g['materials'][1]['normalTexture'] == after.g['materials'][1]['normalTexture'])

def image_data(asset, index):
    view = asset.g['bufferViews'][asset.g['images'][index]['bufferView']]
    offset = view.get('byteOffset', 0)
    return bytes(asset.bin[offset:offset + view['byteLength']])

sizes = [len(image_data(after, index)) for index in range(len(after.g['images']))]
check('every texture below 100 KB', max(sizes) < 100000)
check('GLB below 3 MB', len(after.raw) < 3000000)
check('hair normal bytes preserved', image_data(before, 2) == image_data(after, 2))
body_parameters = np.asarray(Image.open(BytesIO(image_data(after, 3))).convert('RGBA')) / 255
check('packed roughness channel in expected range', body_parameters[:, :, 1].min() >= .61 and body_parameters[:, :, 1].max() <= .93)
check('packed specular channel in expected range', body_parameters[:, :, 3].min() >= .11 and body_parameters[:, :, 3].max() <= .29)
for index, material in enumerate(after.g['materials'][:6]):
    texture = material['pbrMetallicRoughness']['metallicRoughnessTexture']
    expected = {'index': 4 if index == 1 else 3, 'texCoord': 1 if index == 1 else 0}
    check(f'material {index} surface map routing', texture == expected)
    check(f'material {index} specular map routing', material['extensions']['KHR_materials_specular']['specularTexture'] == expected)

def linear(values):
    return np.where(values <= .04045, values / 12.92, ((values + .055) / 1.055) ** 2.4)

def srgb(values):
    return np.where(values <= .0031308, values * 12.92, 1.055 * np.maximum(values, 0) ** (1 / 2.4) - .055)

def sample(asset, mesh_name):
    primitive = asset.prim(mesh_name)
    material = asset.g['materials'][primitive['material']]['pbrMetallicRoughness']
    texture = material['baseColorTexture']
    texture_definition = asset.g['textures'][texture['index']]
    image_index = texture_definition.get('source', texture_definition.get('extensions', {}).get('EXT_texture_webp', {}).get('source'))
    image = linear(np.asarray(Image.open(BytesIO(image_data(asset, image_index))).convert('RGB')) / 255)
    uv = asset.arr(primitive['attributes']['TEXCOORD_' + str(texture.get('texCoord', 0))])
    height, width = image.shape[:2]
    xy = uv * (width, height) - .5
    lo = np.floor(xy).astype(int)
    fraction = xy - lo
    lo[:, 0] = np.clip(lo[:, 0], 0, width - 2)
    lo[:, 1] = np.clip(lo[:, 1], 0, height - 2)
    a = image[lo[:, 1], lo[:, 0]] * (1 - fraction[:, :1]) + image[lo[:, 1], lo[:, 0] + 1] * fraction[:, :1]
    b = image[lo[:, 1] + 1, lo[:, 0]] * (1 - fraction[:, :1]) + image[lo[:, 1] + 1, lo[:, 0] + 1] * fraction[:, :1]
    result = a * (1 - fraction[:, 1:]) + b * fraction[:, 1:]
    return srgb(result * np.array(material.get('baseColorFactor', [1, 1, 1, 1])[:3])) * 255

seams = {}
for label, first_name, second_name in [('neck', 'SM_Character_Face', 'SM_Character_Hair'),
                                      ('cuffs', 'SM_Character_Hands', 'SM_Cloth_Hoodie')]:
    first_positions = before.pos(first_name)
    first_colors = sample(before, first_name)
    lookup = {tuple(point): index for index, point in enumerate(np.round(before.pos(second_name), 6))}
    pairs = []
    for index, point in enumerate(np.round(first_positions, 6)):
        if tuple(point) not in lookup:
            continue
        color = first_colors[index]
        if label == 'neck' and not (point[1] < 1.58 and color[0] > 140 and color[1] > 85):
            continue
        pairs.append((index, lookup[tuple(point)]))
    pairs = np.array(pairs)
    check(label + ' has shared boundary samples', len(pairs) > 10)
    row = {'samples': len(pairs)}
    for version, asset in [('v25', before), ('v26', after)]:
        difference = abs(sample(asset, first_name)[pairs[:, 0]] - sample(asset, second_name)[pairs[:, 1]])
        row[version + '_mean_rgb_gap_0_255'] = round(float(difference.mean()), 3)
    check(label + ' color discontinuity reduced by at least half', row['v26_mean_rgb_gap_0_255'] < row['v25_mean_rgb_gap_0_255'] * .5)
    seams[label] = row

compression = {}
for label in ['body-albedo', 'hair-albedo']:
    reference = np.asarray(Image.open(root / f'work/{label}-v26-reference.png').convert('RGB')).astype(float)
    compressed = np.asarray(Image.open(root / f'work/{label}-v26.webp').convert('RGB')).astype(float)
    difference = abs(reference - compressed)
    compression[label] = {'mean_rgb_error_0_255': round(float(difference.mean()), 3),
                          'rgb_error_p99_0_255': round(float(np.percentile(difference, 99)), 3)}
    if label == 'body-albedo':
        face = after.prim('SM_Character_Face')
        coordinates = after.arr(face['attributes']['TEXCOORD_0']) * reference.shape[:2][::-1]
        triangles = after.arr(face['indices']).reshape(-1, 3)
        mask_image = Image.new('L', reference.shape[:2][::-1], 0)
        draw = ImageDraw.Draw(mask_image)
        for triangle in triangles:
            draw.polygon([tuple(coordinates[index]) for index in triangle], fill=255)
        face_error = difference[np.asarray(mask_image) > 0]
        compression['face_used_texels'] = {'mean_rgb_error_0_255': round(float(face_error.mean()), 3),
                                            'rgb_error_p99_0_255': round(float(np.percentile(face_error, 99)), 3)}
report = {'checks_passed': sum(checks.values()), 'checks_failed': 0, 'glb_bytes': len(after.raw),
          'texture_bytes': sizes, 'seams': seams, 'compression': compression, 'checks': checks}
(root / 'work/material26-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != 'checks'}))
