import json,struct,hashlib
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
def load(p):
 b=p.read_bytes(); n=struct.unpack_from('<I',b,12)[0]; return json.loads(b[20:20+n]),b[28+n:]
src=Path(r'D:\omni-workstation\projects\ZacharyPortfolio\public\models\zachary_character.glb')
a,ab=load(src); b,bb=load(root/'outputs/zachary_character_v21_candidate.glb')
def arr(g,buf,i):
 x=g['accessors'][i]; v=g['bufferViews'][x['bufferView']]; types={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}; cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
 return np.frombuffer(buf,dtype=types[x['componentType']],count=x['count']*cols[x['type']],offset=v.get('byteOffset',0)+x.get('byteOffset',0)).reshape(x['count'],-1)
checks=[]
def check(name,test):
 assert test,name
 checks.append({'check':name,'result':'PASS'})
check('Original source SHA-256 unchanged',hashlib.sha256(src.read_bytes()).hexdigest()==json.loads((root/'outputs/avatar-v21-metrics.json').read_text())['source_sha256'])
check('All node transforms and hierarchy preserved',a['nodes']==b['nodes'])
check('Joint ordering preserved',a['skins'][0]['joints']==b['skins'][0]['joints'])
check('Inverse bind matrices preserved',np.array_equal(arr(a,ab,a['skins'][0]['inverseBindMatrices']),arr(b,bb,b['skins'][0]['inverseBindMatrices'])))
for i in range(6):
 pa=a['meshes'][i]['primitives'][0]; pb=b['meshes'][i]['primitives'][0]
 for key in ['JOINTS_0','WEIGHTS_0','TEXCOORD_0']:
  check(a['meshes'][i]['name']+' '+key+' preserved',np.array_equal(arr(a,ab,pa['attributes'][key]),arr(b,bb,pb['attributes'][key])))
 check(a['meshes'][i]['name']+' topology preserved',np.array_equal(arr(a,ab,pa['indices']),arr(b,bb,pb['indices'])))
for ti,(ta,tb) in enumerate(zip(a['meshes'][0]['primitives'][0]['targets'],b['meshes'][0]['primitives'][0]['targets'])):
 if ti not in [4,5]:
  check('Facial expression displacement preserved',all(np.array_equal(arr(a,ab,ta[k]),arr(b,bb,tb[k])) for k in ta))
 else:
  delta=arr(b,bb,tb['POSITION']); check('Corrected blink finite and below 12mm displacement',bool(np.isfinite(delta).all() and np.linalg.norm(delta,axis=1).max()<0.012))
check('Eight facial expressions',len(b['meshes'][0]['primitives'][0]['targets'])==8)
for m in b['meshes']:
 for p in m['primitives']:
  pos=arr(b,bb,p['attributes']['POSITION']); inds=arr(b,bb,p['indices'])
  check(m['name']+' finite positions / valid triangles',bool(np.isfinite(pos).all() and inds.max()<len(pos) and len(inds)%3==0))
  normal=arr(b,bb,p['attributes']['NORMAL']); check(m['name']+' finite unit normals',bool(np.isfinite(normal).all() and np.max(np.abs(np.linalg.norm(normal,axis=1)-1))<0.002))
  if 'WEIGHTS_0' in p['attributes']:
   weights=arr(b,bb,p['attributes']['WEIGHTS_0']); check(m['name']+' normalized four-influence skinning',bool(weights.shape[1]==4 and np.max(np.abs(weights.sum(axis=1)-1))<0.001))
def image(g,buf):
 v=g['bufferViews'][g['images'][0]['bufferView']]; return buf[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
check('Embedded source texture byte-identical',image(a,ab)==image(b,bb))
check('Candidate below 3 MB', (root/'outputs/zachary_character_v21_candidate.glb').stat().st_size<3_000_000)
result={'passed':len(checks),'failed':0,'checks':checks,'not_covered':['Browser performance timings','Visual likeness acceptance','Collision-free full motion range','Anatomical eyelid topology and mouth cavity quality']}
(root/'outputs/avatar-v21-validation.json').write_text(json.dumps(result,indent=2)); print(json.dumps({'passed':len(checks),'failed':0,'not_covered':result['not_covered']}))
