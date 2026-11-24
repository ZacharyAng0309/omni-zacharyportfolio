"""Compress Cycles bakes and embed them without rebuilding the rig or morphs."""
from pathlib import Path
from PIL import Image
import numpy as np,json
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];work=root/'work';a=Asset(work/'hair38-shape.glb');report={}
albedo=Image.open(work/'hair38-albedo-raw.png').convert('RGB');path=work/'hair38-albedo.webp'
for quality in range(90,19,-5):
 albedo.save(path,quality=quality,method=6)
 if path.stat().st_size<100000:break
assert path.stat().st_size<100000
decoded=np.asarray(Image.open(path)).astype(float);source=np.asarray(albedo).astype(float)
report['albedo']={'bytes':path.stat().st_size,'resolution':list(albedo.size),'quality':quality,'mean_channel_error_255':float(np.abs(source-decoded).mean())}
raw=Image.open(work/'hair38-normal-raw.png').convert('RGB');path=work/'hair38-normal.webp'
raw.save(path,quality=95,method=6)
assert path.stat().st_size<100000
x=np.asarray(raw).astype(float)/127.5-1;y=np.asarray(Image.open(path).convert('RGB').resize(raw.size,Image.Resampling.BILINEAR)).astype(float)/127.5-1
valid=(x[:,:,2]>.1)&(np.linalg.norm(x,axis=2)>.6)
x/=np.maximum(np.linalg.norm(x,axis=2,keepdims=True),1e-8);y/=np.maximum(np.linalg.norm(y,axis=2,keepdims=True),1e-8)
angle=np.degrees(np.arccos(np.clip(np.sum(x*y,axis=2),-1,1)))[valid]
report['normal']={'bytes':path.stat().st_size,'resolution':list(raw.size),'webp_quality':95,'angular_error_degrees_percentiles':np.percentile(angle,[50,95,99,100]).tolist()}
assert np.percentile(angle,95)<4
parameters=Image.open(work/'hair38-parameters-raw.png').convert('RGBA');path=work/'hair38-parameters.png'
values=np.asarray(parameters).copy();values[:,:,1]=np.minimum(255,np.round(values[:,:,1]/4)*4).astype('u1');values[:,:,3]=np.minimum(255,np.round(values[:,:,3]/4)*4).astype('u1')
Image.fromarray(values).save(path,optimize=True);assert path.stat().st_size<100000
report['parameters']={'bytes':path.stat().st_size,'resolution':list(parameters.size),'maximum_scalar_quantization_error':float(np.abs(values.astype(float)-np.asarray(parameters)).max()/255)}
replacements={}
for i,label,extension in [(1,'albedo','webp'),(2,'normal','webp'),(4,'parameters','png')]:
 im=a.g['images'][i];im['name']='T_Hair_v38_'+label;im['mimeType']='image/'+extension;replacements[im['bufferView']]=(work/f'hair38-{label}.{extension}').read_bytes()
a.g['textures'][2].pop('source',None);a.g['textures'][2]['extensions']={'EXT_texture_webp':{'source':2}}
binary=bytearray()
for i,v in enumerate(a.g['bufferViews']):
 start=v.get('byteOffset',0);data=replacements.get(i,a.bin[start:start+v['byteLength']]);binary.extend(b'\0'*((-len(binary))%4));v['byteOffset']=len(binary);v['byteLength']=len(data);binary.extend(data)
binary.extend(b'\0'*((-len(binary))%4));a.bin=binary;a.g['buffers'][0]['byteLength']=len(binary);a.g['materials'][a.prim('SM_Character_Hair')['material']]['name']='M_Hair_v38_CurtainFlow'
path=root/'outputs/zachary_character_v38_candidate.glb';a.save(path);report['glb_bytes']=path.stat().st_size
(work/'hair38-textures.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
