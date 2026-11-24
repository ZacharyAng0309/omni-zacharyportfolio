from kinematics27 import *
import json
before=Asset(root/'outputs/zachary_character_v28_candidate.glb');after=Asset(root/'outputs/zachary_character_v29_candidate.glb')
checks={}
def check(name,value):
    checks[name]=bool(value);assert value,name
for field in ['meshes','materials','images','textures','samplers','skins','scenes','nodes']:
    check(field+' preserved',before.g[field]==after.g[field])
attrs=before.prim('SM_Character_Hands')['attributes'];allowed={attrs[key] for key in ['POSITION','NORMAL','JOINTS_0','WEIGHTS_0']}
for i in range(len(before.g['accessors'])):
    if i not in allowed:check(f'accessor {i} preserved',np.array_equal(before.arr(i),after.arr(i)))
for i,image in enumerate(before.g['images']):
    view=before.g['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0);length=view['byteLength']
    check(f'image {i} bytes preserved',before.bin[offset:offset+length]==after.bin[offset:offset+length])
    check(f'image {i} below 100 KB',length<100000)
old=before.pos('SM_Character_Hands');new=after.pos('SM_Character_Hands')
keys=set(map(tuple,np.rint(before.pos('SM_Cloth_Hoodie').astype(float)*1e6).astype(np.int64)))
seam=[i for i,point in enumerate(old) if tuple(np.rint(point.astype(float)*1e6).astype(np.int64)) in keys]
check('all 101 cuff vertices identified',len(seam)==101)
for key in ['POSITION','NORMAL','JOINTS_0','WEIGHTS_0']:
    check('cuff '+key+' preserved',np.array_equal(before.arr(attrs[key])[seam],after.arr(attrs[key])[seam]))
displacement=np.linalg.norm(new-old,axis=1)*1000
check('hand surface displacement below 1.501 mm',displacement.max()<1.501)
tri=after.arr(after.prim('SM_Character_Hands')['indices']).reshape(-1,3)
oldcross=np.cross(old[tri[:,1]]-old[tri[:,0]],old[tri[:,2]]-old[tri[:,0]])
newcross=np.cross(new[tri[:,1]]-new[tri[:,0]],new[tri[:,2]]-new[tri[:,0]])
check('no reversed hand triangles',np.all(np.einsum('ij,ij->i',oldcross,newcross)>0))
check('no degenerate hand triangles',np.min(np.linalg.norm(newcross,axis=1))>1e-9)
normal=after.arr(attrs['NORMAL'])
check('hand normals normalized',np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-5)
weights=after.arr(attrs['WEIGHTS_0']);joints=after.arr(attrs['JOINTS_0'])
check('hand weights normalized',np.max(abs(weights.sum(axis=1)-1))<1e-6)
check('hand weights nonnegative',np.min(weights)>=0)
check('maximum four influences',weights.shape[1]==4)
check('valid bone indices',int(joints.max())<len(after.g['skins'][0]['joints']))
check('GLB below 3 MB',len(after.raw)<3000000)
report={'checks_passed':sum(checks.values()),'checks_failed':0,'glb_bytes':len(after.raw),
        'max_hand_surface_change_mm':float(displacement.max()),'cuff_vertices_preserved':len(seam),'checks':checks}
(root/'work/hand29-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({key:value for key,value in report.items() if key!='checks'}))
