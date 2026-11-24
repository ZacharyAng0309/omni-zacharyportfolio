import bpy,sys,json,copy,numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
b=Asset(root/'outputs/zachary_character_v36_candidate.glb');a=Asset(root/'work/zachary_character_v37_tuning.glb');p=a.prim('SM_Character_Face');lids=a.prim('SM_Character_Eyelids');checks={};metrics={}
def check(name,value):
 checks[name]=bool(value)
 if not value:print('FAIL',name)
changed=set()
for name in ['SM_Character_Face','SM_Character_Hair','SM_Character_Eyelids','SM_Character_EyeLeft','SM_Character_EyeRight']:
 prim=a.prim(name)
 changed.update(prim['attributes'][sem] for sem in ['POSITION','NORMAL'])
 if name in ['SM_Character_EyeLeft','SM_Character_EyeRight']:changed.add(prim['attributes']['COLOR_0'])
for k,t in enumerate(lids['targets']):
 changed.add(t['NORMAL'])
 if k in [4,5]:changed.add(t['POSITION'])
for i in range(len(a.g['accessors'])):
 check(f'Accessor {i} finite',np.isfinite(a.arr(i)).all())
 if i not in changed:check(f'Accessor {i} preserved',np.array_equal(a.arr(i),b.arr(i)))
for field in ['meshes','nodes','skins','images','textures','samplers']:check(field+' preserved',a.g[field]==b.g[field])
eye_material=a.prim('SM_Character_EyeLeft')['material']
for i,mat in enumerate(b.g['materials']):
 if i!=eye_material:check(f'Material {i} preserved',mat==a.g['materials'][i])
for i,img in enumerate(a.g['images']):
 v=a.g['bufferViews'][img['bufferView']];off=v.get('byteOffset',0);check(f'Texture {i} preserved',a.bin[off:off+v['byteLength']]==b.bin[off:off+v['byteLength']]);check(f'Texture {i} budget',v['byteLength']<100000)
for name in ['SM_Character_Face','SM_Character_Hair']:
 old=b.pos(name);x=a.pos(name);delta=x-old
 check(name+' X/Z preserved',np.array_equal(x[:,[0,2]],old[:,[0,2]]))
 check(name+' placement bounded',np.max(abs(delta[:,1]))<.001601)
 check(name+' lower face and rear unchanged',not np.any(delta[(old[:,1]<1.560)|(old[:,2]<.045)]))
 hp=b.pos('SM_Character_Hair');fp=b.pos('SM_Character_Face');hm={tuple(np.rint(v.astype(float)*1e6).astype('i8')):j for j,v in enumerate(hp)}
 pairs=[(i,hm[tuple(np.rint(v.astype(float)*1e6).astype('i8'))]) for i,v in enumerate(fp) if tuple(np.rint(v.astype(float)*1e6).astype('i8')) in hm]
check('Hair/face seam maintained',max(np.linalg.norm(a.pos('SM_Character_Face')[i]-a.pos('SM_Character_Hair')[j]) for i,j in pairs)<1e-6)
oral=a.prim('SM_Character_OralCavity');active=np.unique(a.arr(oral['indices']))
for sem,i in oral['attributes'].items():check('Active oral '+sem+' preserved',np.array_equal(a.arr(i)[active],b.arr(i)[active]))
metrics['shared_hair_seam_pairs']=len(pairs)
rings=json.loads((root/'work/eye36-rings.json').read_text());facepos=a.arr(p['attributes']['POSITION']);lidpos=a.arr(lids['attributes']['POSITION']);lookup={tuple(np.rint(v.astype(float)*1e6).astype('i8')):i for i,v in enumerate(facepos)}
for side in rings:
 for index in side['boundary_indices']:
  source=lookup[tuple(np.rint(lidpos[index].astype(float)*1e6).astype('i8'))]
  check(f'Seam {index} rest',np.linalg.norm(lidpos[index]-facepos[source])<1e-6)
  for k in range(8):check(f'Seam {index} target {k}',np.linalg.norm(a.arr(lids['targets'][k]['POSITION'])[index]-a.arr(p['targets'][k]['POSITION'])[source])<1e-6)
newnames=['SM_Character_Eyelids','SM_Character_EyeLeft','SM_Character_EyeRight']
for name in newnames:
 prim=a.prim(name);x=a.arr(prim['attributes']['POSITION']);t=a.arr(prim['indices']).reshape(-1,3);n=a.arr(prim['attributes']['NORMAL']);w=a.arr(prim['attributes']['WEIGHTS_0']);j=a.arr(prim['attributes']['JOINTS_0'])
 check(name+' valid indices',t.min()>=0 and t.max()<len(x));check(name+' unit normals',np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-5);check(name+' normalized weights',np.max(abs(w.sum(1)-1))<1e-6);check(name+' head attachment',np.all(j[:,0]==32) and np.allclose(w[:,0],1));check(name+' nonzero area',np.min(np.linalg.norm(np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]]),axis=1))>1e-12)
 edges=Counter(tuple(sorted((int(i),int(j)))) for row in t for i,j in [(row[0],row[1]),(row[1],row[2]),(row[2],row[0])]);check(name+' no nonmanifold edges',max(edges.values())<=2)
 if name!='SM_Character_Eyelids':check(name+' closed globe',min(edges.values())==2)
 metrics[name]={'vertices':len(x),'triangles':len(t),'edge_multiplicities':dict(Counter(edges.values()))}
def posed(prim,values):
 x=a.arr(prim['attributes']['POSITION']).copy()
 for k,target in enumerate(prim.get('targets',[])):x+=a.arr(target['POSITION'])*values.get(k,0)
 return x
def polygon_inside(q,poly):
 yes=False
 for i,v in enumerate(poly):
  u=poly[i-1]
  if (v[1]>q[1])!=(u[1]>q[1]) and q[0]<(u[0]-v[0])*(q[1]-v[1])/(u[1]-v[1])+v[0]:yes=not yes
 return yes
cases={'neutral':{},'quarter-blink':{4:.25,5:.25},'half-blink':{4:.5,5:.5},'three-quarter-blink':{4:.75,5:.75},'full-blink':{4:1,5:1},'blink-brow':{4:1,5:1,6:1},'left-wink':{4:1},'right-wink':{5:1},'brow':{6:1},'speech':{7:.65,2:.35}}
visibility={}
for label,values in cases.items():
 pos=[];tris=[]
 for prim in [p,lids]:
  xx=posed(prim,values);tris.extend((a.arr(prim['indices']).reshape(-1,3)+len(pos)).tolist());pos.extend(xx.tolist())
 tree=BVHTree.FromPolygons([Vector(v) for v in pos],tris,all_triangles=True);lp=posed(lids,values);row={}
 for side in rings:
  name='SM_Character_EyeLeft' if side['sign']==1 else 'SM_Character_EyeRight';ep=a.prim(name);xx=a.pos(name);tt=a.arr(ep['indices']).reshape(-1,3);samples=np.concatenate([xx,xx[tt].mean(1)])
  visible=0;outside=0;poly=lp[side['rings'][2],:2]
  for q in samples:
   hit,normal,index,dist=tree.ray_cast(Vector((q[0],q[1],.3)),Vector((0,0,-1)),.6)
   if hit is None or q[2]>hit.z+1e-5:
    visible+=1
    if not polygon_inside(q[:2],poly):outside+=1
  row[name]={'visible_samples':visible,'outside_aperture_samples':outside};check(label+' '+name+' no skin breakthrough',outside==0)
  if values.get(4 if side['sign']==1 else 5,0)==1:check(label+' '+name+' full closure',visible==0)
  if values.get(4 if side['sign']==1 else 5,0)==0:check(label+' '+name+' eye visible',visible>0)
 visibility[label]=row
 for name,prim in [('face',p),('eyelids',lids)]:
  xx=posed(prim,values);tt=a.arr(prim['indices']).reshape(-1,3);cc=np.cross(xx[tt[:,1]]-xx[tt[:,0]],xx[tt[:,2]]-xx[tt[:,0]])
  check(label+' '+name+' no zero-area triangles',np.min(np.linalg.norm(cc,axis=1))>1e-12)
  if name=='eyelids':check(label+' eyelid fronts retain orientation',np.all(cc[:,2]>-1e-11))
combined_points=np.concatenate([a.arr(pr['attributes']['POSITION']) for pr in [p,lids,a.prim('SM_Character_OralCavity')]])
_,inv=np.unique(np.rint(combined_points.astype(float)*1e6).astype('i8'),axis=0,return_inverse=True);offset=0;ec=Counter()
for pr in [p,lids,a.prim('SM_Character_OralCavity')]:
 tt=inv[a.arr(pr['indices']).reshape(-1,3)+offset];offset+=len(a.arr(pr['attributes']['POSITION']));ec.update(tuple(sorted((int(i),int(j)))) for row in tt for i,j in [(row[0],row[1]),(row[1],row[2]),(row[2],row[0])])
check('Combined skin no nonmanifold edges',max(ec.values())<=2);check('Only two 32-edge apertures added',sum(n==1 for n in ec.values())==196+64)
metrics['combined_skin_edge_multiplicities']=dict(Counter(ec.values()))
for name in ['SM_Character_Face','SM_Character_Hair']:
 pr=a.prim(name);oldpr=b.prim(name);tt=a.arr(pr['indices']).reshape(-1,3)
 for label,values in cases.items():
  old=b.pos(name).copy();new=posed(pr,values)
  for k,target in enumerate(oldpr.get('targets',[])):old+=b.arr(target['POSITION'])*values.get(k,0)
  c0=np.cross(old[tt[:,1]]-old[tt[:,0]],old[tt[:,2]]-old[tt[:,0]]);c1=np.cross(new[tt[:,1]]-new[tt[:,0]],new[tt[:,2]]-new[tt[:,0]])
  valid=np.linalg.norm(c0,axis=1)>1e-12
  check(name+' '+label+' no new orientation reversal',np.all(np.sum(c0[valid]*c1[valid],axis=1)>0))
metrics.update(visibility=visibility,glb_bytes=len(a.raw),triangles=sum(a.arr(p['indices']).size//3 for m in a.g['meshes'] for p in m['primitives']))
check('Under 3 MB',len(a.raw)<3000000);check('Under 45000 triangles',metrics['triangles']<=45000)
report={'checks_passed':sum(checks.values()),'checks_failed':sum(not v for v in checks.values()),'metrics':metrics,'checks':checks};(root/'work/eye37-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
