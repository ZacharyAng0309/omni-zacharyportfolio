from pathlib import Path
import numpy as np,json,copy
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];a=Asset(root/'work/hair42-shape.glb');fibers=np.load(root/'work/hair42-filaments.npz')
def append_view(data,target=None):
 a.bin.extend(b'\0'*((-len(a.bin))%4));v={'buffer':0,'byteOffset':len(a.bin),'byteLength':len(data)}
 if target:v['target']=target
 a.g['bufferViews'].append(v);a.bin.extend(data);return len(a.g['bufferViews'])-1
def accessor(data,kind,component,target=34962):
 data=np.ascontiguousarray(data);view=append_view(data.tobytes(),target);i=len(a.g['accessors']);a.g['accessors'].append({'bufferView':view,'componentType':component,'count':len(data),'type':kind,'min':data.min(axis=0).reshape(-1).tolist(),'max':data.max(axis=0).reshape(-1).tolist()});return i
attributes={}
for name,kind,component in [('POSITION','VEC3',5126),('NORMAL','VEC3',5126),('COLOR_0','VEC4',5126),('JOINTS_0','VEC4',5123),('WEIGHTS_0','VEC4',5126)]:attributes[name]=accessor(fibers[name],kind,component)
indices=accessor(fibers['indices'].reshape(-1,1),'SCALAR',5123,34963)
material=len(a.g['materials']);a.g['materials'].append({'name':'M_Hair_Filaments_v42','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'roughnessFactor':.54,'metallicFactor':0},'extensions':{'KHR_materials_specular':{'specularFactor':.22}},'doubleSided':False,'alphaMode':'OPAQUE'})
mesh=len(a.g['meshes']);a.g['meshes'].append({'name':'SM_Character_HairFilaments','primitives':[{'attributes':attributes,'indices':indices,'material':material}]})
oldnode=next(i for i,n in enumerate(a.g['nodes']) if n.get('name')=='SM_Character_Hair');node=copy.deepcopy(a.g['nodes'][oldnode]);node.update(name='SM_Character_HairFilaments',mesh=mesh);node.pop('children',None);index=len(a.g['nodes']);a.g['nodes'].append(node)
parents=[n for n in a.g['nodes'][:-1] if oldnode in n.get('children',[])]
if parents:
 for parent in parents:parent['children'].append(index)
else:
 for scene in a.g['scenes']:
  if oldnode in scene.get('nodes',[]):scene['nodes'].append(index)
a.bin.extend(b'\0'*((-len(a.bin))%4));a.g['buffers'][0]['byteLength']=len(a.bin);path=root/'outputs/zachary_character_v42_candidate.glb';a.save(path);print('CANDIDATE',path.stat().st_size,'filament triangles',len(fibers['indices']))
