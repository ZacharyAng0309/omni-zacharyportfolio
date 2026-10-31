import json,struct,hashlib
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
source=root/'outputs/zachary_character_v21_candidate.glb'
raw=source.read_bytes(); size=struct.unpack_from('<I',raw,12)[0]; g=json.loads(raw[20:20+size]); binary=bytearray(raw[28+size:])
def array(i):
 a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]
 dtype={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]; c={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 return np.frombuffer(binary,dtype=dtype,count=a['count']*c,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,c)
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
def relax(pos,tri):
 _,inv=np.unique(np.round(pos,6),axis=0,return_inverse=True); count=inv.max()+1
 p=np.zeros((count,3)); np.add.at(p,inv,pos); p/=np.bincount(inv)[:,None]
 edge=np.sort(inv[np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]])],axis=1); edge,n=np.unique(edge,axis=0,return_counts=True); boundary=np.unique(edge[n==1])
 for _ in range(3):
  sums=np.zeros_like(p); degree=np.zeros(count)
  for i,j in [(0,1),(1,0)]: np.add.at(sums,edge[:,i],p[edge[:,j]]); np.add.at(degree,edge[:,i],1)
  delta=(sums/np.maximum(degree[:,None],1)-p)*0.25; delta[boundary]=0; p+=delta
 return p[inv]-pos
def normal(pos,tri):
 _,inv=np.unique(np.round(pos,6),axis=0,return_inverse=True); summed=np.zeros((inv.max()+1,3))
 fn=np.cross(pos[tri[:,1]]-pos[tri[:,0]],pos[tri[:,2]]-pos[tri[:,0]])
 for i in range(3): np.add.at(summed,inv[tri[:,i]],fn)
 out=summed[inv]; return out/np.maximum(np.linalg.norm(out,axis=1)[:,None],1e-12)
other=set()
for mesh in g['meshes'][2:6]:
 for p in mesh['primitives']: other.update(map(tuple,np.round(array(p['attributes']['POSITION']),6)))
hair=g['meshes'][1]['primitives'][0]; hp=array(hair['attributes']['POSITION']); other.update(map(tuple,np.round(hp,6)))
face=g['meshes'][0]['primitives'][0]; pos=array(face['attributes']['POSITION']); old=pos.copy(); tri=array(face['indices']).reshape(-1,3).astype(int)
pinned=np.array([tuple(p) in other for p in np.round(pos,6)])
x,y,z=old.T
# Shorten the lower-face profile and broaden the jaw slightly; preserve orbits,
# nose bridge and shared boundaries, with continuous falloff into the neck.
w=smooth(1.440,1.475,y)*(1-smooth(1.525,1.585,y))*smooth(0.015,0.055,z)*(1-pinned)
pos[:,1]+=0.006*w
pos[:,0]+=0.0015*np.tanh(x/0.035)*w
# Ear contour relaxation in welded space. Protect the attachment and temple seat.
ear=smooth(0.067,0.080,np.abs(x))*smooth(1.525,1.547,y)*(1-smooth(1.582,1.596,y))*(1-smooth(0.010,0.045,z))*(1-pinned)
d=relax(old,tri); length=np.linalg.norm(d,axis=1); d*=np.minimum(1,0.002/np.maximum(length,1e-12))[:,None]
pos+=d*ear[:,None]
norm=array(face['attributes']['NORMAL']); nn=normal(pos,tri); blend=ear[:,None]*0.55; norm[:]=norm*(1-blend)+nn*blend; norm[:]/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
hair_old=hp.copy(); x,y,z=hair_old.T
# Modest silhouette reduction above the hairline, never moving seam vertices.
w=smooth(1.665,1.730,y)
face_keys=set(map(tuple,np.round(old,6)))
hair_pinned=np.array([tuple(v) in face_keys for v in np.round(hair_old,6)])
w*=1-hair_pinned
hp[:,0]*=1-0.04*w
hp[:,1]-=0.006*smooth(1.665,1.745,y)*(1-hair_pinned)
hp[:,2]+=0.007*smooth(0.025,0.12,-z)*w
for mesh in g['meshes']:
 for p in mesh['primitives']:
  for key in ['POSITION','NORMAL']:
   i=p['attributes'][key]; g['accessors'][i]['min']=array(i).min(axis=0).tolist(); g['accessors'][i]['max']=array(i).max(axis=0).tolist()
g['asset']['generator']='Omni avatar v22 portrait-guided candidate'
def save():
 j=json.dumps(g,separators=(',',':')).encode(); j+=b' '*((-len(j))%4)
 data=struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\0')+binary
 (root/'outputs/zachary_character_v22_candidate.glb').write_bytes(data)
save()
report={'v21_sha256':hashlib.sha256(raw).hexdigest(),'face_max_delta_mm':float(np.linalg.norm(pos-old,axis=1).max()*1000),'ear_max_relax_mm':float(np.linalg.norm(d*ear[:,None],axis=1).max()*1000),'hair_max_delta_mm':float(np.linalg.norm(hp-hair_old,axis=1).max()*1000),'face_pinned_vertices':int(pinned.sum()),'seam_displacement_mm':float(np.linalg.norm(pos[pinned]-old[pinned],axis=1).max()*1000)}
(root/'outputs/avatar-v22-metrics.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
