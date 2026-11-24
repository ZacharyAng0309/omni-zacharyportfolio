from pathlib import Path
import numpy as np,json
from glb_asset import Asset
root=Path(__file__).resolve().parents[1]
before=Asset(root/'outputs/zachary_character_v30_candidate.glb');after=Asset(root/'outputs/zachary_character_v31_candidate.glb')
checks={}
def check(name,value):checks[name]=bool(value);assert value,name
for field in ['meshes','nodes','skins','materials','textures','images','samplers','scenes']:
    check(field+' preserved',before.g[field]==after.g[field])
p=before.prim('SM_Character_Face');allowed={p['targets'][i]['POSITION'] for i in [4,5]}
for i in range(len(before.g['accessors'])):
    if i not in allowed:check(f'accessor {i} preserved',np.array_equal(before.arr(i),after.arr(i)))
for i,image in enumerate(before.g['images']):
    view=before.g['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0);size=view['byteLength']
    check(f'image {i} bytes preserved',before.bin[offset:offset+size]==after.bin[offset:offset+size])
    check(f'image {i} below 100 KB',size<100000)
points=before.pos('SM_Character_Face');hair=before.pos('SM_Character_Hair')
hairkeys=set(map(tuple,np.rint(hair.astype(float)*1e6).astype(np.int64)))
shared=[i for i,v in enumerate(points) if tuple(np.rint(v.astype(float)*1e6).astype(np.int64)) in hairkeys]
check('128 face/hair seam copies found',len(shared)==128)
old_seam=[];new_seam=[]
for target,center in [(4,.034),(5,-.034)]:
    index=p['targets'][target]['POSITION'];old=before.arr(index);new=after.arr(index)
    check(f'target {target} finite',np.all(np.isfinite(new)))
    check(f'target {target} bounds updated',np.allclose(after.g['accessors'][index]['min'],new.min(axis=0)) and np.allclose(after.g['accessors'][index]['max'],new.max(axis=0)))
    check(f'target {target} upper forehead protected',np.all(new[points[:,1]>=1.612]==0))
    check(f'target {target} face/hair seam fixed',np.all(new[shared]==0))
    # Allow sub-millimeter differences from evaluating the field on the current
    # rest mesh, while guarding the established lower-lid closure.
    lower=points[:,1]<=1.605
    check(f'target {target} lower closure changes below 0.25 mm',np.max(np.linalg.norm(old[lower]-new[lower],axis=1))*1000<.25)
    core=(abs(points[:,0]-center)<.012)&(abs(points[:,1]-1.598)<.006)&(points[:,2]>.075)
    check(f'target {target} eye aperture sampled',sum(core)>3)
    before_height=np.ptp(points[core,1]);after_height=np.ptp((points+new)[core,1])
    check(f'target {target} closure reduces aperture over 95 percent',after_height<before_height*.05)
    old_seam.append(float(np.linalg.norm(old[shared],axis=1).max()*1000));new_seam.append(float(np.linalg.norm(new[shared],axis=1).max()*1000))
check('GLB below 3 MB',len(after.raw)<3000000)
report={'checks_passed':sum(checks.values()),'checks_failed':0,'glb_bytes':len(after.raw),
        'old_max_face_hair_blink_seam_mm':max(old_seam),'new_max_face_hair_blink_seam_mm':max(new_seam),'checks':checks}
(root/'work/blink31-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
