from pathlib import Path
from collections import Counter
import sys,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
before=Asset(root/'outputs/zachary_character_v32_candidate.glb');after=Asset(root/'outputs/zachary_character_v33_candidate.glb')
checks={};metrics={}
def check(name,value):
    checks[name]=bool(value)
    if not value:print('FAIL',name)
for i in range(len(before.g['accessors'])):check(f'Existing accessor {i} unchanged',np.array_equal(before.arr(i),after.arr(i)))
for field in ['meshes','materials']:
    check('Existing '+field+' unchanged',after.g[field][:len(before.g[field])]==before.g[field])
for field in ['skins','images','textures','samplers']:check(field+' unchanged',after.g[field]==before.g[field])
for i,image in enumerate(before.g['images']):
    view=before.g['bufferViews'][image['bufferView']];start=view.get('byteOffset',0);end=start+view['byteLength']
    check(f'Texture {i} preserved',before.bin[start:end]==after.bin[start:end]);check(f'Texture {i} below 100 KB',end-start<100000)
check('Avatar below 3 MB',len(after.raw)<3000000)
new_meshes=after.g['meshes'][len(before.g['meshes']):]
check('Three oral meshes added',len(new_meshes)==3)
for i in range(len(before.g['accessors']),len(after.g['accessors'])):check(f'New accessor {i} finite',np.isfinite(after.arr(i)).all())
topology={}
for mesh in new_meshes:
    name=mesh['name'];p=mesh['primitives'][0];x=after.arr(p['attributes']['POSITION']);t=after.arr(p['indices']).reshape(-1,3)
    check(name+' valid indices',t.min()>=0 and t.max()<len(x))
    edges=Counter(tuple(sorted((int(a),int(b)))) for tri in t for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])])
    check(name+' closed manifold components',all(n==2 for n in edges.values()))
    area=np.linalg.norm(np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]]),axis=1)/2
    check(name+' no zero-area triangles',area.min()>1e-12)
    volume=float(np.sum(np.einsum('ij,ij->i',x[t[:,0]],np.cross(x[t[:,1]],x[t[:,2]])))/6)
    check(name+' outward winding',volume>0)
    weights=after.arr(p['attributes']['WEIGHTS_0']);joints=after.arr(p['attributes']['JOINTS_0'])
    check(name+' rigid head attachment',np.all(joints[:,0]==32) and np.all(weights[:,0]==1) and np.all(weights[:,1:]==0))
    check(name+' unit normals',np.max(abs(np.linalg.norm(after.arr(p['attributes']['NORMAL']),axis=1)-1))<1e-5)
    check(name+' matching facial names',mesh['extras']['targetNames']==before.g['meshes'][0]['extras']['targetNames'] if 'targetNames' in before.g['meshes'][0].get('extras',{}) else mesh['extras']['targetNames']==next(m for m in before.g['meshes'] if m['name']=='SM_Character_Face')['extras']['targetNames'])
    for i,target in enumerate(p['targets']):
        for semantic,index in target.items():
            ar=after.arr(index);acc=after.g['accessors'][index]
            check(f'{name} target {i} {semantic} bounds',np.allclose(acc['min'],ar.min(0)) and np.allclose(acc['max'],ar.max(0)))
    topology[name]={'vertices':len(x),'triangles':len(t),'volume_m3':volume,'edge_multiplicity':dict(Counter(edges.values()))}
poses={'neutral':{},'jaw':{'jawOpen':.45},'speech':{'viseme_aa':.65,'mouthOpen':.35},'smile-speech':{'mouthSmileLeft':.42,'mouthSmileRight':.42,'viseme_aa':.65,'mouthOpen':.35},'wide':{'jawOpen':1,'mouthOpen':1},'aa':{'viseme_aa':1},'asymmetric-speech':{'mouthSmileLeft':.6,'mouthOpen':.4}}
face=next(m for m in after.g['meshes'] if m['name']=='SM_Character_Face')
def posed(mesh,values):
    p=mesh['primitives'][0];x=after.arr(p['attributes']['POSITION']).copy()
    for name,target in zip(mesh['extras']['targetNames'],p['targets']):x+=after.arr(target['POSITION'])*values.get(name,0)
    return x

for label,values in poses.items():
 trees=[]
 for mesh in new_meshes:
  points=posed(mesh,values);tri=after.arr(mesh['primitives'][0]['indices']).reshape(-1,3)
  trees.append(BVHTree.FromPolygons([Vector(p) for p in points],tri.tolist(),all_triangles=True))
 print(label,[(new_meshes[i]['name'],new_meshes[j]['name'],len(trees[i].overlap(trees[j]))) for i,j in [(0,1),(0,2),(1,2)]])
