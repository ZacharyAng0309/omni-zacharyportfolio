import json,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]; path=root/'outputs/zachary_character_v22_candidate.glb'
raw=path.read_bytes(); n=struct.unpack_from('<I',raw,12)[0]; g=json.loads(raw[20:20+n]); binary=bytearray(raw[28+n:])
indices={}
for label in ['albedo','normal']:
 ext='webp' if label=='albedo' else 'png'
 blob=(root/f'outputs/hair-v22-{label}.{ext}').read_bytes()
 while len(binary)%4: binary.append(0)
 view=len(g['bufferViews']); g['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(blob)}); binary.extend(blob)
 im=len(g['images']); g['images'].append({'bufferView':view,'mimeType':'image/webp' if label=='albedo' else 'image/png','name':'T_Hair_v22_'+label})
 indices[label]=len(g['textures']); g['textures'].append({'extensions':{'EXT_texture_webp':{'source':im}},'sampler':0} if label=='albedo' else {'source':im,'sampler':0})
while len(binary)%4: binary.append(0)
g['buffers'][0]['byteLength']=len(binary)
mat=g['materials'][1]; mat['pbrMetallicRoughness'].update(baseColorTexture={'index':indices['albedo']},baseColorFactor=[1,1,1,1],roughnessFactor=0.68)
mat['normalTexture']={'index':indices['normal'],'scale':1.0}; mat['extensions']['KHR_materials_specular']['specularFactor']=0.24
j=json.dumps(g,separators=(',',':')).encode(); j+=b' '*((-len(j))%4)
path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\0')+binary)
print('Candidate bytes:',path.stat().st_size)
