from pathlib import Path
from collections import Counter
import json,numpy as np
from glb_asset import Asset
root=Path(__file__).resolve().parents[1]
b=Asset(root/'outputs/zachary_character_v33_candidate.glb');a=Asset(root/'outputs/zachary_character_v34_candidate.glb')
bp=b.prim('SM_Character_Face');p=a.prim('SM_Character_Face');checks={};metrics={}
def check(name,value):
 checks[name]=bool(value)
 if not value:print('FAIL',name)
for field in ['nodes','skins','samplers'] :check(field+' preserved',b.g[field]==a.g[field])
changed=set(bp['attributes'].values())|{bp['indices']}|{t['POSITION'] for t in bp['targets']}
for i in range(len(b.g['accessors'])):
 if i not in changed:check(f'Unaffected accessor {i}',np.array_equal(a.arr(i),b.arr(i)))
for semantic,i in bp['attributes'].items():
 if semantic!='NORMAL':check('Original face '+semantic,np.array_equal(a.arr(p['attributes'][semantic])[:2614],b.arr(i)))
for k,(old,new) in enumerate(zip(bp['targets'],p['targets'])):
 delta=a.arr(new['POSITION'])[:2614]-b.arr(old['POSITION'])
 check(f'Target {k} unchanged or bounded blink correction',np.max(abs(delta))<.00003 if k in [4,5] else not np.any(delta))
 check(f'Target {k} bounds',np.allclose(a.g['accessors'][new['POSITION']]['min'],a.arr(new['POSITION']).min(0)) and np.allclose(a.g['accessors'][new['POSITION']]['max'],a.arr(new['POSITION']).max(0)))
for mesh in b.g['meshes']:
 if mesh['name']=='SM_Character_Face':continue
 new=next(m for m in a.g['meshes'] if m['name']==mesh['name']);check(mesh['name']+' structure',mesh==new)
 for oldp,newp in zip(mesh['primitives'],new['primitives']):
  active=np.unique(b.arr(oldp['indices']))
  for sem,i in oldp['attributes'].items():check(mesh['name']+' active '+sem,np.array_equal(b.arr(i)[active],a.arr(newp['attributes'][sem])[active]))
  for k,(ot,nt) in enumerate(zip(oldp.get('targets',[]),newp.get('targets',[]))):
   for sem in ot:check(mesh['name']+f' active target {k} '+sem,np.array_equal(b.arr(ot[sem])[active],a.arr(nt[sem])[active]))
for i,mat in enumerate(b.g['materials']):
 if i!=p['material']:check(f'Material {i} preserved',mat==a.g['materials'][i])
def payload(asset,img):
 v=asset.g['bufferViews'][img['bufferView']];start=v.get('byteOffset',0);return asset.bin[start:start+v['byteLength']]
for i,img in enumerate(a.g['images']):
 check(f'Texture {i} budget',len(payload(a,img))<100000)
 if i<len(b.g['images']):check(f'Texture {i} byte preservation',payload(a,img)==payload(b,b.g['images'][i]))
for i in range(len(a.g['accessors'])):check(f'Finite accessor {i}',np.isfinite(a.arr(i)).all())
x=a.pos('SM_Character_Face');tri=a.arr(p['indices']).reshape(-1,3);patch=np.load(root/'work/eye34-baked-data.npz')['patched']
check('Valid face indices',tri.min()>=0 and tri.max()<len(x))
check('Face normal unit length',np.max(abs(np.linalg.norm(a.arr(p['attributes']['NORMAL']),axis=1)-1))<1e-5)
uv=a.arr(p['attributes']['TEXCOORD_1']);check('New UV in range',uv.min()>=0 and uv.max()<=1)
before_points=b.pos('SM_Character_Face');before_tri=b.arr(bp['indices']).reshape(-1,3);before_uv=b.arr(bp['attributes']['TEXCOORD_0'])
def key(point):return tuple(np.rint(point.astype(float)*1e6).astype('i8'))
source_triangles={tuple(sorted(key(before_points[i]) for i in row)):row for row in before_tri}
uv_errors=[]
for row in tri[~patch]:
 source=source_triangles[tuple(sorted(key(x[i]) for i in row))];mapping={key(before_points[i]):i for i in source}
 expected=before_uv[[mapping[key(x[i])] for i in row]].copy();expected[:,0]*=.5
 uv_errors.append(float(abs(uv[row]-expected).max()))
check('All 2407 unaffected triangle UV samples preserved',max(uv_errors)<1e-7)
check('Eye atlas isolated in right half',uv[tri[patch],0].min()>=.5)
copies=np.load(root/'work/eye34-duplicate-sources.npy')
for semantic,index in p['attributes'].items():
 if semantic!='TEXCOORD_1':check('New seam copies '+semantic,np.array_equal(a.arr(index)[2614:],a.arr(index)[copies]))
def edges(asset,names):
 result=Counter()
 for name in names:
  prim=asset.prim(name);pts=np.rint(asset.arr(prim['attributes']['POSITION'])*1e6).astype('i8');t=asset.arr(prim['indices']).reshape(-1,3)
  result.update(tuple(sorted((tuple(pts[i]),tuple(pts[j])))) for row in t for i,j in [(row[0],row[1]),(row[1],row[2]),(row[2],row[0])])
 return result
for names in [['SM_Character_Face'],['SM_Character_Face','SM_Character_OralCavity']]:
 old=edges(b,names);new=edges(a,names);label='+'.join(names)
 check(label+' no nonmanifold edges',max(new.values())<=2)
 check(label+' exact boundary preservation',{e for e,n in old.items() if n==1}=={e for e,n in new.items() if n==1})
 metrics[label]={'before_edge_multiplicities':dict(Counter(old.values())),'after_edge_multiplicities':dict(Counter(new.values()))}
pose_metrics={}
for left,right,brow in [(0,0,0),(.5,.5,0),(1,1,0),(1,0,0),(0,1,0),(0,0,1),(.5,.5,1),(1,1,1)]:
 y=x.copy()
 for i,weight in [(4,left),(5,right),(6,brow)]:y+=a.arr(p['targets'][i]['POSITION'])*weight
 cross=np.cross(y[tri[:,1]]-y[tri[:,0]],y[tri[:,2]]-y[tri[:,0]])
 label=f'blink {left}/{right}, brow {brow}';flips=int(sum(cross[patch,2]<=0));pose_metrics[label]=flips
 check(label+' patch orientation',flips==0)
 # Shared geometric copies must carry identical blink motion.
for target in [4,5]:
 delta=a.arr(p['targets'][target]['POSITION']);groups={}
 for i,point in enumerate(np.rint(x*1e6).astype('i8')):groups.setdefault(tuple(point),[]).append(i)
 check(f'Blink {target} copies synchronized',all(np.max(np.ptp(delta[ids],axis=0))<1e-7 for ids in groups.values()))
hair=b.pos('SM_Character_Hair');hairset={tuple(v) for v in np.rint(hair*1e6).astype('i8')};seam=[i for i,v in enumerate(np.rint(x*1e6).astype('i8')) if tuple(v) in hairset]
for target in [4,5]:check(f'Blink {target} hair seam fixed',not np.any(a.arr(p['targets'][target]['POSITION'])[seam]))
check('Under 3 MB',len(a.raw)<3000000)
metrics.update(glb_bytes=len(a.raw),triangles=sum(a.arr(pr['indices']).size//3 for m in a.g['meshes'] for pr in m['primitives']),eye_patch_triangles=int(sum(patch)),expression_patch_inversions=pose_metrics,hair_seam_copies=len(seam))
report={'checks_passed':sum(checks.values()),'checks_failed':sum(not v for v in checks.values()),'metrics':metrics,'checks':checks}
(root/'work/eye34-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}));assert report['checks_failed']==0
