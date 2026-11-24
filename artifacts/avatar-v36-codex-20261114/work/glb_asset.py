import json,struct
from pathlib import Path
import numpy as np
class Asset:
 def __init__(self,path):
  self.path=Path(path); self.raw=self.path.read_bytes(); n=struct.unpack_from('<I',self.raw,12)[0]; self.g=json.loads(self.raw[20:20+n]); self.bin=bytearray(self.raw[28+n:])
 def arr(self,i):
  a=self.g['accessors'][i]; v=self.g['bufferViews'][a['bufferView']]; cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]; dt={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
  assert 'byteStride' not in v
  return np.frombuffer(self.bin,dtype=dt,count=a['count']*cols,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,cols)
 def prim(self,name): return next(m for m in self.g['meshes'] if m.get('name')==name)['primitives'][0]
 def pos(self,name): return self.arr(self.prim(name)['attributes']['POSITION'])
 def save(self,path):
  for mesh in self.g['meshes']:
   for p in mesh['primitives']:
    for k in ['POSITION','NORMAL']:
     i=p['attributes'][k]; ar=self.arr(i); self.g['accessors'][i].update(min=ar.min(axis=0).tolist(),max=ar.max(axis=0).tolist())
  j=json.dumps(self.g,separators=(',',':')).encode(); j+=b' '*((-len(j))%4)
  Path(path).write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(self.bin))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(self.bin),b'BIN\0')+self.bin)
