"""Validate the bounded hair edit and preservation of the complete avatar."""
from pathlib import Path
import numpy as np,json,hashlib,io
from PIL import Image
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];before=Asset(root/'outputs/zachary_character_v37_candidate.glb');after=Asset(root/'outputs/zachary_character_v38_candidate.glb');checks=[]
def check(label,result):
 checks.append({'check':label,'passed':bool(result)});assert result,label
p=after.prim('SM_Character_Hair');changed={p['attributes']['POSITION'],p['attributes']['NORMAL']}
check('Accessor count unchanged',len(before.g['accessors'])==len(after.g['accessors']))
for i in range(len(before.g['accessors'])):
 check(f'accessor {i} finite',np.isfinite(after.arr(i)).all())
 if i not in changed:check(f'accessor {i} byte preserved',before.arr(i).tobytes()==after.arr(i).tobytes())
for key in ['meshes','nodes','skins','scenes','scene','animations','extensionsUsed','extensionsRequired','samplers']:
 check(key+' unchanged',before.g.get(key)==after.g.get(key))
for i,(a,b) in enumerate(zip(before.g['materials'],after.g['materials'])):
 if i==p['material']:
  a=dict(a);b=dict(b);a.pop('name',None);b.pop('name',None)
 check(f'material {i} parameters and UV routing unchanged',a==b)
def payload(asset,i):
 v=asset.g['bufferViews'][asset.g['images'][i]['bufferView']];return asset.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
images=[]
for i in range(len(after.g['images'])):
 data=payload(after,i);im=Image.open(io.BytesIO(data));im.load();check(f'image {i} under 100 KB',len(data)<100000)
 if i not in [1,2,4]:check(f'image {i} preserved',data==payload(before,i))
 images.append({'image':i,'bytes':len(data),'resolution':list(im.size),'sha256':hashlib.sha256(data).hexdigest()})
pos=after.pos('SM_Character_Hair');old=before.pos('SM_Character_Hair');delta=pos-old;tri=after.arr(p['indices']).reshape(-1,3)
check('Hair displacement under 5.5 mm',np.linalg.norm(delta,axis=1).max()<.0055)
check('Crown part only changes height',np.array_equal(pos[:,[0,2]],old[:,[0,2]]))
check('All moved vertices in crown brush',np.all(old[np.linalg.norm(delta,axis=1)>1e-8,1]>1.691))
oc=np.cross(old[tri[:,1]]-old[tri[:,0]],old[tri[:,2]]-old[tri[:,0]]);nc=np.cross(pos[tri[:,1]]-pos[tri[:,0]],pos[tri[:,2]]-pos[tri[:,0]])
cos=np.sum(oc*nc,axis=1)/np.maximum(np.linalg.norm(oc,axis=1)*np.linalg.norm(nc,axis=1),1e-15);ratio=np.linalg.norm(nc,axis=1)/np.maximum(np.linalg.norm(oc,axis=1),1e-15)
check('Hair triangle orientation retained',cos.min()>.8);check('Hair triangle area retained',ratio.min()>.65)
normal=after.arr(p['attributes']['NORMAL']);check('Hair normals unit length',np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-4)
fp=before.pos('SM_Character_Face');hm={tuple(np.rint(v.astype(float)*1e6).astype('i8')):j for j,v in enumerate(old)}
pairs=[(i,hm[tuple(np.rint(v.astype(float)*1e6).astype('i8'))]) for i,v in enumerate(fp) if tuple(np.rint(v.astype(float)*1e6).astype('i8')) in hm]
shared=[j for i,j in pairs]
check('Every matched face/hair seam pair preserved',len(pairs)>100 and np.array_equal(pos[shared],old[shared]) and max(np.linalg.norm(after.pos('SM_Character_Face')[i]-pos[j]) for i,j in pairs)<1e-6)
triangles=sum(after.arr(pr['indices']).size//3 for mesh in after.g['meshes'] for pr in mesh['primitives']);size=after.path.stat().st_size;joints=len(after.g['skins'][0]['joints'])
check('Triangle count preserved and within desktop budget',triangles==44910 and triangles<=45000);check('Avatar below 3 MB',size<3000000);check('All 52 joints retained',joints==52)
report={'checks_passed':len(checks),'checks_failed':0,'metrics':{'triangles':triangles,'glb_bytes':size,'joints':joints,'images':images,'moved_hair_vertex_copies':int((np.linalg.norm(delta,axis=1)>1e-8).sum()),'shared_face_hair_copies':len(shared)},'checks':checks}
(root/'work/hair38-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
