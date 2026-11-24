from pathlib import Path
import numpy as np,json,hashlib
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];b=Asset(root/'outputs/zachary_character_v38_candidate.glb');a=Asset(root/'outputs/zachary_character_v39_candidate.glb');checks=[]
def check(label,condition):
 checks.append({'check':label,'passed':bool(condition)});assert condition,label
hp=a.prim('SM_Character_Hair');fp=a.prim('SM_Character_Face');lp=a.prim('SM_Character_Eyelids')
changed={hp['attributes']['POSITION'],hp['attributes']['NORMAL'],fp['attributes']['NORMAL'],lp['attributes']['NORMAL']}|{t['NORMAL'] for t in lp['targets']}
check('Accessor count unchanged',len(a.g['accessors'])==len(b.g['accessors']))
for i in range(len(a.g['accessors'])):
 check(f'Accessor {i} finite',np.isfinite(a.arr(i)).all())
 if i not in changed:check(f'Accessor {i} byte preserved',a.arr(i).tobytes()==b.arr(i).tobytes())
for key in ['meshes','nodes','skins','scenes','scene','materials','textures','images','animations','samplers','extensionsUsed','extensionsRequired']:
 check(key+' preserved',a.g.get(key)==b.g.get(key))
images=[]
for i,image in enumerate(a.g['images']):
 va=a.g['bufferViews'][image['bufferView']];vb=b.g['bufferViews'][b.g['images'][i]['bufferView']];da=a.bin[va['byteOffset']:va['byteOffset']+va['byteLength']];db=b.bin[vb['byteOffset']:vb['byteOffset']+vb['byteLength']]
 check(f'Image {i} byte preserved',da==db);check(f'Image {i} under 100 KB',len(da)<100000);images.append({'image':i,'bytes':len(da)})
old=b.pos('SM_Character_Hair');new=a.pos('SM_Character_Hair');d=new-old;t=a.arr(hp['indices']).reshape(-1,3);moved=np.linalg.norm(d,axis=1)>1e-8
check('Hair movement bounded to 1.601 mm',np.linalg.norm(d,axis=1).max()<.001601)
check('Front fringe and crown part fixed',not np.any(d[(old[:,2]>.065)|(old[:,1]>1.714)]))
cross=lambda x:np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]])
oc,nc=cross(old),cross(new);oa,na=np.linalg.norm(oc,axis=1),np.linalg.norm(nc,axis=1)
check('Hair orientation preserved',np.min(np.sum(oc*nc,axis=1)/np.maximum(oa*na,1e-15))>.8);check('Hair triangle area preserved',np.min(na/np.maximum(oa,1e-15))>.65)
_,inv=np.unique(np.rint(old.astype(float)*1e6).astype('i8'),axis=0,return_inverse=True);lt=inv[t];edges,count=np.unique(np.sort(np.concatenate([lt[:,[0,1]],lt[:,[1,2]],lt[:,[2,0]]]),axis=1),axis=0,return_counts=True);boundary=np.unique(edges[count!=2]);check('Every hair boundary position fixed',not np.any(d[np.isin(inv,boundary)]))
hm={tuple(np.rint(v.astype(float)*1e6).astype('i8')):j for j,v in enumerate(old)};pairs=[(i,hm[tuple(np.rint(v.astype(float)*1e6).astype('i8'))]) for i,v in enumerate(b.pos('SM_Character_Face')) if tuple(np.rint(v.astype(float)*1e6).astype('i8')) in hm]
check('135 hair/face seam pairs preserved',len(pairs)==135 and max(np.linalg.norm(a.pos('SM_Character_Face')[i]-new[j]) for i,j in pairs)<1e-6)
seams=json.loads((root/'work/hair39-seams.json').read_text());normal=np.concatenate([a.arr(p['attributes']['NORMAL']) for p in [fp,lp]])
check('Repaired base normals unit length',np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-5)
for i,group in enumerate(seams['groups']):
 check(f'Shading group {i} rest continuity',np.ptp(normal[group],axis=0).max()<1e-6)
 for k in range(8):
  delta=np.concatenate([np.zeros_like(a.pos('SM_Character_Face')),a.arr(lp['targets'][k]['NORMAL'])]);posed=normal+delta
  check(f'Shading group {i} target {k} continuity',np.ptp(posed[group],axis=0).max()<1e-6)
triangles=sum(a.arr(p['indices']).size//3 for mesh in a.g['meshes'] for p in mesh['primitives']);size=a.path.stat().st_size
check('No experimental fringe mesh exported',not any(m['name']=='SM_Character_HairFringe' for m in a.g['meshes']))
check('Triangle budget',triangles==44910 and triangles<=45000);check('File budget',size<3000000);check('52 joints preserved',len(a.g['skins'][0]['joints'])==52)
report={'checks_passed':len(checks),'checks_failed':0,'metrics':{'triangles':triangles,'glb_bytes':size,'joints':52,'images':images,'hair_vertices_moved':int(moved.sum()),'maximum_hair_movement_mm':float(np.linalg.norm(d,axis=1).max()*1000),'shared_face_hair_pairs':len(pairs),'welded_shading_groups':len(seams['groups'])},'checks':checks}
(root/'work/hair39-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
