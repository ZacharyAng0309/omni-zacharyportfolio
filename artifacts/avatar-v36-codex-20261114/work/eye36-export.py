import json,copy,io,numpy as np
from pathlib import Path
from PIL import Image
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];a=Asset(root/'outputs/zachary_character_v35_candidate.glb');p=a.prim('SM_Character_Face');data=np.load(root/'work/eye36-generated.npz')
face_mesh=next(i for i,m in enumerate(a.g['meshes']) if m['name']=='SM_Character_Face');face_node=next(i for i,n in enumerate(a.g['nodes']) if n.get('mesh')==face_mesh);head_node=next(i for i,n in enumerate(a.g['nodes']) if n.get('name')=='Head');head_joint=a.g['skins'][a.g['nodes'][face_node]['skin']]['joints'].index(head_node)
names=a.g['meshes'][face_mesh]['extras']['targetNames']
for k,delta in zip([4,5],data['face_blinks']):
 index=p['targets'][k]['POSITION'];a.arr(index)[:]=delta;a.g['accessors'][index].update(min=delta.min(0).tolist(),max=delta.max(0).tolist())
def acc(values,kind,component=5126,target=34962):
 ar=np.asarray(values,dtype={5123:'<u2',5126:'<f4'}[component]);a.bin.extend(b'\0'*((-len(a.bin))%4));off=len(a.bin);a.bin.extend(ar.tobytes());vi=len(a.g['bufferViews']);a.g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':ar.nbytes,'target':target});i=len(a.g['accessors']);d={'bufferView':vi,'componentType':component,'count':len(ar),'type':kind}
 if kind=='VEC3':d.update(min=ar.min(0).tolist(),max=ar.max(0).tolist())
 a.g['accessors'].append(d);return i
indices=a.arr(p['indices']).reshape(-1,3).copy()[~data['removed']];p['indices']=acc(indices.reshape(-1,1),'SCALAR',5123,34963)
image=Image.open(root/'work/eye36-lids.png').convert('RGB');buffer=io.BytesIO();image.save(buffer,format='WEBP',quality=95,method=6);payload=buffer.getvalue();assert len(payload)<100000
a.bin.extend(b'\0'*((-len(a.bin))%4));offset=len(a.bin);a.bin.extend(payload);vi=len(a.g['bufferViews']);a.g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(payload)});ii=len(a.g['images']);a.g['images'].append({'bufferView':vi,'mimeType':'image/webp','name':'T_Eyelids_v36'})
texture=copy.deepcopy(a.g['textures'][0]);texture['source']=ii;texture.setdefault('extensions',{})['EXT_texture_webp']={'source':ii};ti=len(a.g['textures']);a.g['textures'].append(texture)
material=copy.deepcopy(a.g['materials'][p['material']]);material['name']='M_Eyelids_v36';material['pbrMetallicRoughness']['baseColorTexture']={'index':ti};lmat=len(a.g['materials']);a.g['materials'].append(material)
emat=len(a.g['materials']);a.g['materials'].append({'name':'M_Eyes_v36','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':.23},'extensions':{'KHR_materials_specular':{'specularFactor':.2}},'doubleSided':False})
def normal(pos,t):
 n=np.zeros_like(pos);c=np.cross(pos[t[:,1]]-pos[t[:,0]],pos[t[:,2]]-pos[t[:,0]])
 for k in range(3):np.add.at(n,t[:,k],c)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);return n
def add(name,points,normals,tri,material,extras,targets=None,skin=None):
 n=len(points)
 if skin is None:
  j=np.zeros((n,4),dtype='u2');j[:,0]=head_joint;w=np.zeros((n,4));w[:,0]=1
 else:j,w=skin
 attributes={'POSITION':acc(points,'VEC3'),'NORMAL':acc(normals,'VEC3'),'JOINTS_0':acc(j,'VEC4',5123),'WEIGHTS_0':acc(w,'VEC4')}
 for key,values in extras.items():attributes[key]=acc(values,'VEC'+str(values.shape[1]))
 primitive={'attributes':attributes,'indices':acc(tri.reshape(-1,1),'SCALAR',5123,34963),'material':material,'mode':4};mesh={'name':name,'primitives':[primitive]}
 if targets is not None:
  boundary=[i for row in json.loads((root/'work/eye36-rings.json').read_text()) for i in row['boundary_indices']];base=normal(points,tri);ts=[]
  for d in targets:
   nd=normal(points+d,tri)-base;nd[boundary]=0;ts.append({'POSITION':acc(d,'VEC3'),'NORMAL':acc(nd,'VEC3')})
  primitive['targets']=ts;mesh.update(extras={'targetNames':names},weights=[0]*8)
 mi=len(a.g['meshes']);a.g['meshes'].append(mesh);node=copy.deepcopy(a.g['nodes'][face_node]);node.update(name=name,mesh=mi);node.pop('children',None);ni=len(a.g['nodes']);a.g['nodes'].append(node)
 parents=[node for node in a.g['nodes'][:-1] if face_node in node.get('children',[])]
 for parent in parents:parent['children'].append(ni)
 if not parents:
  for scene in a.g['scenes']:
   if face_node in scene['nodes']:scene['nodes'].append(ni)
add('SM_Character_Eyelids',data['points'],data['normals'],data['triangles'],lmat,{'TEXCOORD_0':data['uv']},data['morphs'],(data['joints'],data['weights']))
for sign in [-1,1]:
 d=np.load(root/f'work/eye36-globe{sign}.npz');add('SM_Character_EyeRight' if sign<0 else 'SM_Character_EyeLeft',d['points'],d['normals'],d['triangles'],emat,{'COLOR_0':d['colors']})
a.bin.extend(b'\0'*((-len(a.bin))%4));a.g['buffers'][0]['byteLength']=len(a.bin);a.save(root/'work/zachary_character_v36_eye_prototype.glb')
print('PROTOTYPE',len((root/'work/zachary_character_v36_eye_prototype.glb').read_bytes()),'eye skin texture',len(payload),'triangles',sum(a.arr(p['indices']).size//3 for m in a.g['meshes'] for p in m['primitives']))
