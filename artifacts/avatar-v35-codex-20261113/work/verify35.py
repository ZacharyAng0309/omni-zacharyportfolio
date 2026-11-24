from pathlib import Path
from collections import Counter
import json,numpy as np
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];b=Asset(root/'outputs/zachary_character_v34_candidate.glb');a=Asset(root/'outputs/zachary_character_v35_candidate.glb');checks={};metrics={}
def check(name,value):
 checks[name]=bool(value)
 if not value:print('FAIL',name)
changed={a.prim(name)['attributes'][sem] for name in ['SM_Character_Face','SM_Character_Hair'] for sem in ['POSITION','NORMAL']}
for i in range(len(a.g['accessors'])):
 check(f'Accessor {i} finite',np.isfinite(a.arr(i)).all())
 if i not in changed:check(f'Accessor {i} preserved',np.array_equal(a.arr(i),b.arr(i)))
for field in ['meshes','nodes','skins','materials','images','textures','samplers']:check(field+' preserved',a.g[field]==b.g[field])
def payload(asset,img):
 v=asset.g['bufferViews'][img['bufferView']];start=v.get('byteOffset',0);return asset.bin[start:start+v['byteLength']]
for i,img in enumerate(a.g['images']):
 check(f'Texture {i} preserved',payload(a,img)==payload(b,b.g['images'][i]));check(f'Texture {i} below 100 KB',len(payload(a,img))<100000)
names=['SM_Character_Face','SM_Character_Hair'];seams={}
for obj in [a,b]:
 f=obj.pos(names[0]);h=obj.pos(names[1]);hmap={tuple(v):i for i,v in enumerate(np.rint(h.astype(float)*1e6).astype('i8'))}
 if obj==b:pairs=[(i,hmap[tuple(v)]) for i,v in enumerate(np.rint(f.astype(float)*1e6).astype('i8')) if tuple(v) in hmap]
 else:pass
f=a.pos(names[0]);h=a.pos(names[1]);gap=max(np.linalg.norm(f[i]-h[j]) for i,j in pairs);check('All original hair/face seams closed',gap<1e-6);metrics['shared_seam_pairs']=len(pairs);metrics['maximum_seam_gap_mm']=float(gap*1000)
poses=[('neutral',{})]+[(f'target-{k}',{k:1}) for k in range(8)]+[('blink-brow',{4:1,5:1,6:1}),('half-blink',{4:.5,5:.5}),('speech',{7:.65,2:.35}),('smile-speech',{0:.42,1:.42,7:.65,2:.35}),('wide-mouth',{3:1,2:1})]
for name in names:
 p=a.prim(name);x=a.pos(name);old=b.pos(name);t=a.arr(p['indices']).reshape(-1,3);delta=x-old;norm=np.linalg.norm(delta,axis=1)
 check(name+' bounded displacement',norm.max()<.000901);check(name+' unit normals',np.max(abs(np.linalg.norm(a.arr(p['attributes']['NORMAL']),axis=1)-1))<1e-5)
 check(name+' silhouette extremes preserved',np.allclose(x.min(0),old.min(0),atol=1e-7) and np.allclose(x.max(0),old.max(0),atol=1e-7))
 check(name+' no lower-face or ear motion',not np.any(delta[(old[:,1]<1.604)|(abs(old[:,0])>.085)]))
 pose_metrics={}
 for label,values in poses:
  before=old.copy();after=x.copy()
  for k,target in enumerate(p.get('targets',[])):
   d=a.arr(target['POSITION'])*values.get(k,0);before+=d;after+=d
  c0=np.cross(before[t[:,1]]-before[t[:,0]],before[t[:,2]]-before[t[:,0]]);c1=np.cross(after[t[:,1]]-after[t[:,0]],after[t[:,2]]-after[t[:,0]])
  s0=np.linalg.norm(c0,axis=1);s1=np.linalg.norm(c1,axis=1);valid=s0>1e-12;dot=np.sum(c0*c1,axis=1)
  check(name+' '+label+' orientation preserved',np.all(dot[valid]>0))
  check(name+' '+label+' no collapsed triangles',np.all(s1[valid]>.5*s0[valid]))
  pose_metrics[label]={'minimum_relative_area':float((s1[valid]/s0[valid]).min()),'new_orientation_reversals':int(sum(dot[valid]<=0))}
 metrics[name]={'moved_vertex_copies':int(sum(norm>1e-7)),'maximum_displacement_mm':float(norm.max()*1000),'poses':pose_metrics}
 if name=='SM_Character_Face':
  for k in [4,5]:check(f'Blink {k} rest surface unchanged',not np.any(delta[np.linalg.norm(a.arr(p['targets'][k]['POSITION']),axis=1)>0]))
  patch=np.load(root/'work/eye34-baked-data.npz')['patched']
  for label,values in poses:
   if label not in ['neutral','blink-brow','half-blink','target-4','target-5','target-6']:continue
   pos=x.copy()
   for k,target in enumerate(p['targets']):pos+=a.arr(target['POSITION'])*values.get(k,0)
   c=np.cross(pos[t[:,1]]-pos[t[:,0]],pos[t[:,2]]-pos[t[:,0]])
   check('Repaired eye patches '+label+' no inversions',np.all(c[patch,2]>0))
oral=a.prim('SM_Character_OralCavity');active=np.unique(a.arr(oral['indices']))
for sem,index in oral['attributes'].items():check('Active oral '+sem+' preserved',np.array_equal(a.arr(index)[active],b.arr(index)[active]))
# Combined logical topology retains edge multiplicities; coordinates alone changed.
def edges(obj):
 allpoints=np.concatenate([obj.pos(n) for n in names]);_,inv=np.unique(np.rint(allpoints.astype(float)*1e6).astype('i8'),axis=0,return_inverse=True);off=0;count=Counter()
 for n in names:
  p=obj.prim(n);t=inv[a.arr(p['indices']).reshape(-1,3)+off];off+=len(obj.pos(n));count.update(tuple(sorted((int(i),int(j)))) for row in t for i,j in [(row[0],row[1]),(row[1],row[2]),(row[2],row[0])])
 return Counter(count.values())
check('Combined topology multiplicities preserved',edges(a)==edges(b));check('GLB under 3 MB',len(a.raw)<3000000)
metrics.update(glb_bytes=len(a.raw),triangles=sum(a.arr(p['indices']).size//3 for m in a.g['meshes'] for p in m['primitives']))
report={'checks_passed':sum(checks.values()),'checks_failed':sum(not v for v in checks.values()),'metrics':metrics,'checks':checks};(root/'work/verify35.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}));assert report['checks_failed']==0
