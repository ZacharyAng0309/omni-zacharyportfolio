"""Versioned, rig-preserving avatar refinement. Does not overwrite input assets."""
import json,struct,copy,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
src=Path(r'D:\omni-workstation\projects\ZacharyPortfolio\public\models\zachary_character.glb')
b=src.read_bytes(); n=struct.unpack_from('<I',b,12)[0]; g=json.loads(b[20:20+n]); binary=b[28+n:]; original=copy.deepcopy(g)
types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def read(i):
 a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]; assert 'byteStride' not in v
 return np.frombuffer(binary,dtype=types[a['componentType']],count=a['count']*cols[a['type']],offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],cols[a['type']]).copy()
arrays={i:read(i) for i in range(len(g['accessors']))}
def weld(pos):
 _,inv=np.unique(np.round(pos,6),axis=0,return_inverse=True)
 return inv
def smooth_positions(pos,tri,cap=0.0006):
 inv=weld(pos); count=inv.max()+1; p=np.zeros((count,3)); np.add.at(p,inv,pos); p/=np.bincount(inv)[:,None]
 edges=np.sort(np.concatenate((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]])),axis=1)
 edges=inv[edges]; edges=np.sort(edges,axis=1); edges,multiplicity=np.unique(edges,axis=0,return_counts=True)
 boundary=np.unique(edges[multiplicity==1]); start=p.copy()
 for _ in range(2):
  sums=np.zeros_like(p); degree=np.zeros(count)
  for i,j in [(0,1),(1,0)]: np.add.at(sums,edges[:,i],p[edges[:,j]]); np.add.at(degree,edges[:,i],1)
  delta=(sums/np.maximum(degree[:,None],1)-p)*0.22; delta[boundary]=0
  length=np.linalg.norm(delta,axis=1); delta*=np.minimum(1,cap/2/np.maximum(length,1e-12))[:,None]; p+=delta
 return pos+(p-start)[inv]
def normals(pos,tri):
 inv=weld(pos); summed=np.zeros((inv.max()+1,3)); face=np.cross(pos[tri[:,1]]-pos[tri[:,0]],pos[tri[:,2]]-pos[tri[:,0]])
 for c in range(3): np.add.at(summed,inv[tri[:,c]],face)
 out=summed[inv]; return (out/np.maximum(np.linalg.norm(out,axis=1)[:,None],1e-12)).astype('<f4')
changes=[]
for mesh in g['meshes'][:6]:
 p=mesh['primitives'][0]; pi=p['attributes']['POSITION']; ni=p['attributes']['NORMAL']; pos=arrays[pi]; tri=arrays[p['indices']].reshape(-1,3).astype(int); new=pos.copy()
 if mesh['name']=='SM_Character_Face':
  new=smooth_positions(pos,tri)
 if mesh['name']=='SM_Character_Hair':
  # A smooth crown taper leaves the lower fringe and face/hair boundary fixed.
  t=np.clip((pos[:,1]-1.64)/0.1184,0,1); w=t*t*(3-2*t)
  new[:,1]-=0.013*w
  new[:,0]*=1-0.035*w
  new[:,2]*=1-0.05*w
 if not np.array_equal(new,pos):
  arrays[pi]=new.astype('<f4')
  # Retain the source's authored smooth normal field. Reconstructing it from
  # the scan's irregular triangles introduced visible cheek and neck facets.
  changes.append({'mesh':mesh['name'],'max_displacement_mm':float(np.linalg.norm(new-pos,axis=1).max()*1000)})
faceprim=g['meshes'][0]['primitives'][0]
facepos=arrays[faceprim['attributes']['POSITION']]
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
for target_index,cx in [(4,0.034),(5,-0.034)]:
 x,height,depth=facepos.T
 wx=1-smooth(0.012,0.025,np.abs(x-cx))
 wy=1-smooth(0.007,0.022,np.abs(height-1.598))
 front=smooth(0.045,0.075,depth)
 delta=np.zeros_like(facepos); delta[:,1]=-0.97*(height-1.598)*wx*wy*front
 arrays[faceprim['targets'][target_index]['POSITION']]=delta
newprims=[]
def add(array,kind,ctype):
 i=len(g['accessors']); g['accessors'].append({'componentType':ctype,'count':len(array),'type':kind}); arrays[i]=np.asarray(array,dtype=types[ctype]); return i
for part in json.loads((ROOT/'work/glasses-simplified.json').read_text()):
 pos=np.asarray(part['positions'],dtype='<f4'); tri=np.asarray(part['indices'],dtype='<u2')
 newprims.append({'attributes':{'POSITION':add(pos,'VEC3',5126),'NORMAL':add(normals(pos,tri),'VEC3',5126)},'indices':add(tri.reshape(-1,1),'SCALAR',5123),'material':part['material'],'mode':4})
g['meshes'][6]['primitives']=newprims
settings={
 'Zachary_Face_Albedo':(0,0.62,0.28,[0.86,0.83,0.81,1]),
 'Zachary_Hands_Albedo':(0,0.64,0.28,[0.86,0.83,0.81,1]),
 'Zachary_Hair_Albedo':(0,0.72,0.22,[0.65,0.61,0.58,1]),
 'Zachary_Cloth_Hoodie':(0,0.94,0.12,[0.70,0.70,0.72,1]),
 'Zachary_Cloth_Trousers':(0,0.90,0.16,[0.80,0.80,0.82,1]),
 'Zachary_Cloth_Footwear':(0,0.72,0.25,[0.80,0.80,0.82,1]),
 'Glasses_Lens':(0,0.06,0.25,[0.98,0.99,1,0.004])}
for mat in g['materials']:
 if mat['name'] in settings:
  metal,rough,spec,color=settings[mat['name']]; p=mat['pbrMetallicRoughness']; p.update(metallicFactor=metal,roughnessFactor=rough,baseColorFactor=color)
  mat.setdefault('extensions',{})['KHR_materials_specular']={'specularFactor':spec}
# Compact only referenced accessors. Preserve every joint transform, weight, UV and image byte.
used=set()
for mesh in g['meshes']:
 for p in mesh['primitives']:
  used.update(p['attributes'].values()); used.add(p['indices'])
  for t in p.get('targets',[]): used.update(t.values())
for skin in g.get('skins',[]): used.add(skin['inverseBindMatrices'])
mapping={old:i for i,old in enumerate(sorted(used))}; views=[]; out=bytearray(); accessors=[]
def pack(data,target=None):
 while len(out)%4: out.append(0)
 v={'buffer':0,'byteOffset':len(out),'byteLength':len(data)}
 if target: v['target']=target
 views.append(v); out.extend(data); return len(views)-1
for old in sorted(used):
 a=copy.deepcopy(g['accessors'][old]); arr=arrays[old]; a.pop('byteOffset',None); a['bufferView']=pack(arr.tobytes())
 if 'min' in a or a['type']=='VEC3': a['min']=arr.min(axis=0).tolist(); a['max']=arr.max(axis=0).tolist()
 accessors.append(a)
for mesh in g['meshes']:
 for p in mesh['primitives']:
  p['attributes']={k:mapping[v] for k,v in p['attributes'].items()}; p['indices']=mapping[p['indices']]
  p['targets']=[{k:mapping[v] for k,v in t.items()} for t in p.get('targets',[])]
  if not p['targets']: del p['targets']
for skin in g.get('skins',[]): skin['inverseBindMatrices']=mapping[skin['inverseBindMatrices']]
for im in g['images']:
 v=original['bufferViews'][im['bufferView']]; image_bytes=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]; im['bufferView']=pack(image_bytes)
while len(out)%4: out.append(0)
g['accessors']=accessors; g['bufferViews']=views; g['buffers']=[{'byteLength':len(out)}]
g.setdefault('asset',{})['generator']='Omni avatar v21 candidate; original rig and texture retained'
j=json.dumps(g,separators=(',',':')).encode(); j+=b' '*((-len(j))%4)
result=struct.pack('<4sII',b'glTF',2,28+len(j)+len(out))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(out),b'BIN\0')+out
dest=ROOT/'outputs/zachary_character_v21_candidate.glb'; dest.write_bytes(result)
before=sum(original['accessors'][p['indices']]['count']//3 for m in original['meshes'] for p in m['primitives'])
after=sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives'])
report={'source_sha256':hashlib.sha256(b).hexdigest(),'source_bytes':len(b),'candidate_bytes':len(result),'triangles_before':before,'triangles_after':after,'changes':changes,'rig_node_transforms_identical':g['nodes']==original['nodes'],'embedded_texture_unchanged':True,'facial_target_count':len(g['meshes'][0]['primitives'][0]['targets']),'corrected_targets':['eyeBlinkLeft','eyeBlinkRight'],'unchanged_expression_targets':6}
(ROOT/'outputs/avatar-v21-metrics.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
