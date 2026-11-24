import bpy,sys,json,copy,numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
b=Asset(root/'outputs/zachary_character_v35_candidate.glb');a=Asset(root/'work/zachary_character_v36_eye_prototype.glb');p=a.prim('SM_Character_Face');bp=b.prim('SM_Character_Face');lids=a.prim('SM_Character_Eyelids');checks={};metrics={}
def check(name,value):
 checks[name]=bool(value)
 if not value:print('FAIL',name)
changed={p['targets'][k]['POSITION'] for k in [4,5]}
for i in range(len(b.g['accessors'])):
 if i not in changed:check(f'Original accessor {i} preserved',np.array_equal(a.arr(i),b.arr(i)))
for i in range(len(a.g['accessors'])):check(f'Accessor {i} finite',np.isfinite(a.arr(i)).all())
oldnodes=copy.deepcopy(a.g['nodes'][:len(b.g['nodes'])])
for node in oldnodes:
 if 'children' in node:node['children']=[i for i in node['children'] if i<len(b.g['nodes'])]
check('Existing node transforms preserved',oldnodes==b.g['nodes'])
check('Existing materials preserved',a.g['materials'][:len(b.g['materials'])]==b.g['materials'])
for field in ['skins','samplers']:check(field+' preserved',a.g[field]==b.g[field])
for mesh in b.g['meshes']:
 if mesh['name']!='SM_Character_Face':check(mesh['name']+' structure',mesh==next(m for m in a.g['meshes'] if m['name']==mesh['name']))
for i,img in enumerate(a.g['images']):
 v=a.g['bufferViews'][img['bufferView']];start=v.get('byteOffset',0);payload=a.bin[start:start+v['byteLength']];check(f'Texture {i} budget',len(payload)<100000)
 if i<len(b.g['images']):
  ov=b.g['bufferViews'][b.g['images'][i]['bufferView']];off=ov.get('byteOffset',0);check(f'Original texture {i} preserved',payload==b.bin[off:off+ov['byteLength']])
for k in [4,5]:
 old=b.arr(bp['targets'][k]['POSITION']);new=a.arr(p['targets'][k]['POSITION']);check(f'Blink {k} XY preserved',np.array_equal(old[:,:2],new[:,:2]));check(f'Blink {k} inactive vertices preserved',np.array_equal(old[np.linalg.norm(old,axis=1)==0],new[np.linalg.norm(old,axis=1)==0]))
 metrics[f'blink_{k}_maximum_added_depth_mm']=float(np.max(abs(old[:,2]-new[:,2]))*1000)
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
metrics.update(visibility=visibility,glb_bytes=len(a.raw),triangles=sum(a.arr(p['indices']).size//3 for m in a.g['meshes'] for p in m['primitives']))
check('Under 3 MB',len(a.raw)<3000000);check('Under 45000 triangles',metrics['triangles']<=45000)
report={'checks_passed':sum(checks.values()),'checks_failed':sum(not v for v in checks.values()),'metrics':metrics,'checks':checks};(root/'work/eye36-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
