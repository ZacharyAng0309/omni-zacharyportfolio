"""Preservation, topology and rig checks for the v42 hair-only refinement."""
import json,hashlib,numpy as np
from pathlib import Path
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];before=Asset(root/'outputs/zachary_character_v41_candidate.glb');after=Asset(root/'outputs/zachary_character_v42_candidate.glb')
checks=[];metrics={}
def check(name,condition,detail=None):
 checks.append({'check':name,'passed':bool(condition),'detail':detail})
def raw_view(asset,index):
 v=asset.g['bufferViews'][index];off=v.get('byteOffset',0);return asset.bin[off:off+v['byteLength']]
hp=before.prim('SM_Character_Hair');allowed={hp['attributes']['POSITION'],hp['attributes']['NORMAL']}
for i in range(len(before.g['accessors'])):
 if i not in allowed:check(f'Original accessor {i} unchanged',np.array_equal(before.arr(i),after.arr(i)))
for i in range(len(after.g['accessors'])):check(f'Accessor {i} finite',np.isfinite(after.arr(i)).all())
for field in ['skins','textures','samplers','images','extensionsUsed','extensionsRequired','animations']:
 check(field+' retained',before.g.get(field)==after.g.get(field))
check('All original meshes and primitives retained',before.g['meshes']==after.g['meshes'][:-1])
check('All original materials retained',before.g['materials']==after.g['materials'][:-1])
for i,old in enumerate(before.g['nodes']):
 new=dict(after.g['nodes'][i]);new['children']=[j for j in new.get('children',[]) if j<len(before.g['nodes'])]
 if 'children' not in old and not new['children']:new.pop('children')
 check(f'Original node {i} retained',old==new)
for i,image in enumerate(before.g['images']):check(f'Image {i} byte identical',raw_view(before,image['bufferView'])==raw_view(after,image['bufferView']))
old=before.pos('SM_Character_Hair').copy();new=after.pos('SM_Character_Hair').copy();delta=np.linalg.norm(new-old,axis=1);tri=after.arr(hp['indices']).reshape(-1,3)
metrics['crown_vertices_moved']=int(np.sum(delta>1e-8));metrics['crown_max_displacement_mm']=float(delta.max()*1000)
check('Crown movement at most 1.801 mm',delta.max()<=.001801)
check('Lower fringe and ear hair boundary unchanged',np.array_equal(old[old[:,1]<=1.685],new[old[:,1]<=1.685]))
facekeys=set(map(tuple,np.rint(before.pos('SM_Character_Face').astype(float)*1e6).astype('i8')))
seam=np.array([tuple(p) in facekeys for p in np.rint(old.astype(float)*1e6).astype('i8')]);metrics['face_hair_seam_copies']=int(seam.sum())
check('Every original Face-Hair seam position retained',np.array_equal(old[seam],new[seam]))
oc=np.cross(old[tri[:,1]]-old[tri[:,0]],old[tri[:,2]]-old[tri[:,0]]);nc=np.cross(new[tri[:,1]]-new[tri[:,0]],new[tri[:,2]]-new[tri[:,0]])
ol=np.linalg.norm(oc,axis=1);nl=np.linalg.norm(nc,axis=1);cos=np.sum(oc*nc,axis=1)/np.maximum(ol*nl,1e-25);ratio=nl/np.maximum(ol,1e-25)
check('Original hair triangles preserve orientation',cos.min()>.85,float(cos.min()));check('Original hair triangle areas preserved',ratio.min()>.72,float(ratio.min()))
fp=after.prim('SM_Character_HairFilaments');pos=after.arr(fp['attributes']['POSITION']);normal=after.arr(fp['attributes']['NORMAL']);fib=after.arr(fp['indices']).reshape(-1,3)
weights=after.arr(fp['attributes']['WEIGHTS_0']);joints=after.arr(fp['attributes']['JOINTS_0'])
check('Filament indices in range',fib.min()>=0 and fib.max()<len(pos))
check('Filament normals unit length',np.max(np.abs(np.linalg.norm(normal,axis=1)-1))<1e-5)
check('Filament weights normalized and nonnegative',np.min(weights)>=0 and np.max(np.abs(weights.sum(axis=1)-1))<1e-6)
check('Filament joints valid',joints.max()<len(after.g['skins'][0]['joints']))
head=next(i for i,j in enumerate(after.g['skins'][0]['joints']) if after.g['nodes'][j].get('name')=='Head')
headweight=np.sum(weights*(joints==head),axis=1);check('Every filament vertex follows Head exactly',np.max(np.abs(headweight-1))<1e-6)
check('Filaments share the existing hair skin',next(n for n in after.g['nodes'] if n.get('name')=='SM_Character_HairFilaments')['skin']==next(n for n in after.g['nodes'] if n.get('name')=='SM_Character_Hair')['skin'])
cross=np.cross(pos[fib[:,1]].astype(float)-pos[fib[:,0]],pos[fib[:,2]].astype(float)-pos[fib[:,0]]);areas=np.linalg.norm(cross,axis=1)*.5
metrics['smallest_filament_triangle_area_m2']=float(areas.min());check('Filament triangles nondegenerate',areas.min()>1e-14)
all_edges=np.concatenate([fib[:,[0,1]],fib[:,[1,2]],fib[:,[2,0]]]);edges,count=np.unique(np.sort(all_edges,axis=1),axis=0,return_counts=True)
check('Filaments are closed manifold tubes',np.all(count==2))
forward=set(map(tuple,all_edges));check('Consistent outward winding at every edge',all(tuple(x[::-1]) in forward for x in all_edges))
report=json.loads((root/'work/hair42-build.json').read_text());volumes=[]
for i,strand in enumerate(report['strand_ranges']):
 lo=strand['first'];hi=lo+strand['count'];face=fib[(fib.min(axis=1)>=lo)&(fib.max(axis=1)<hi)];v=pos.astype(float)-pos[lo].astype(float)
 volume=np.sum(v[face[:,0]]*np.cross(v[face[:,1]],v[face[:,2]]))/6;volumes.append(volume);check(f'Filament {i} positive enclosed volume',volume>0,float(volume))
metrics.update(filaments=len(volumes),filament_vertices=len(pos),filament_triangles=len(fib),triangles=sum(after.arr(p['indices']).size//3 for m in after.g['meshes'] for p in m['primitives']),glb_bytes=len(after.raw),images=len(after.g['images']),joints=len(after.g['skins'][0]['joints']),glb_sha256=hashlib.sha256(after.raw).hexdigest())
check('Candidate below 3 MB',metrics['glb_bytes']<3000000);check('Candidate below 50000 triangles',metrics['triangles']<50000)
check('No extra texture images',metrics['images']==7);check('52 original joints',metrics['joints']==52)
for i,img in enumerate(after.g['images']):check(f'Image {i} below 100 KB',len(raw_view(after,img['bufferView']))<100000)
result={'checks_passed':sum(c['passed'] for c in checks),'checks_failed':sum(not c['passed'] for c in checks),'metrics':metrics,'checks':checks}
(root/'work/hair42-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
assert result['checks_failed']==0,[c for c in checks if not c['passed']]
