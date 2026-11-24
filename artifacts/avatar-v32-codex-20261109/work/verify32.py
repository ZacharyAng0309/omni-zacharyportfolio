from pathlib import Path
from collections import Counter,defaultdict
import numpy as np,json
from glb_asset import Asset
root=Path(__file__).resolve().parents[1]
before=Asset(root/'outputs/zachary_character_v31_candidate.glb');after=Asset(root/'outputs/zachary_character_v32_candidate.glb')
checks={};metrics={}
def check(name,value):
    checks[name]=bool(value)
    if not value:print('FAIL',name)
bp=before.prim('SM_Character_Face');p=after.prim('SM_Character_Face');oral=after.prim('SM_Character_OralCavity')
allowed=set(bp['attributes'].values())|{bp['indices']}|{t['POSITION'] for t in bp['targets']}
for i in range(len(before.g['accessors'])):
    if i not in allowed:check(f'Unrelated accessor {i} preserved',np.array_equal(before.arr(i),after.arr(i)))
for i in range(len(after.g['accessors'])):check(f'Accessor {i} finite',np.isfinite(after.arr(i)).all())
for field in ['skins','textures','images','samplers']:
    check(field+' preserved',before.g[field]==after.g[field])
for name,index in bp['attributes'].items():
    check('Original face '+name+' preserved',np.array_equal(before.arr(index),after.arr(p['attributes'][name])[:len(before.arr(index))]))
for i in [0,1,4,5,6]:check(f'Original expression {i} preserved',np.array_equal(before.arr(bp['targets'][i]['POSITION']),after.arr(p['targets'][i]['POSITION'])[:len(before.pos('SM_Character_Face'))]))
for i,image in enumerate(before.g['images']):
    view=before.g['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0);size=view['byteLength']
    check(f'Image {i} bytes preserved',before.bin[offset:offset+size]==after.bin[offset:offset+size]);check(f'Image {i} under 100 KB',size<100000)
check('Oral mesh shares target and attribute accessors',p['targets']==oral['targets'] and p['attributes']==oral['attributes'])
check('GLB under 3 MB',len(after.raw)<3000000)
x=after.pos('SM_Character_Face');tri=np.concatenate([after.arr(q['indices']).reshape(-1,3) for q in [p,oral]])
check('All face indices valid',tri.min()>=0 and tri.max()<len(x))
weights=after.arr(p['attributes']['WEIGHTS_0']);check('Weights normalized',np.max(abs(weights.sum(1)-1))<1e-5)
check('Weights nonnegative',weights.min()>=0)
normals=after.arr(p['attributes']['NORMAL']);check('New normals unit length',np.max(abs(np.linalg.norm(normals[len(before.pos('SM_Character_Face')):],axis=1)-1))<1e-5)
def topology(asset):
    x=asset.pos('SM_Character_Face');ts=[asset.arr(asset.prim('SM_Character_Face')['indices']).reshape(-1,3)]
    if any(m['name']=='SM_Character_OralCavity' for m in asset.g['meshes']):ts.append(asset.arr(asset.prim('SM_Character_OralCavity')['indices']).reshape(-1,3))
    t=np.concatenate(ts);area=np.linalg.norm(np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]]),axis=1)/2;t=t[area>1e-12]
    keys=[tuple(row) for row in np.rint(x.astype(float)*1e6).astype(np.int64)]
    edges=Counter(tuple(sorted((keys[a],keys[b]))) for row in t for a,b in [(row[0],row[1]),(row[1],row[2]),(row[2],row[0])])
    return {e for e,n in edges.items() if n==1},{e:n for e,n in edges.items() if n>2},dict(Counter(edges.values())),int(sum(area<=1e-12))
bb,bn,bc,bd=topology(before);ab,an,ac,ad=topology(after)
check('No new welded boundary edges',ab==bb)
check('No new nonmanifold edges',an==bn)
metrics.update(baseline_edge_multiplicity=bc,candidate_edge_multiplicity=ac,baseline_degenerate_triangles=bd,candidate_degenerate_triangles=ad)
groups=defaultdict(list)
for i in np.unique(tri):groups[tuple(np.rint(x[i].astype(float)*1e6).astype(np.int64))].append(int(i))
new_seams=[ids for ids in groups.values() if len(ids)>1 and max(ids)>=len(before.pos('SM_Character_Face'))]
check('New surface seam samples present',len(new_seams)>10)
for i,t in enumerate(p['targets']):
    d=after.arr(t['POSITION']);acc=after.g['accessors'][t['POSITION']]
    check(f'Target {i} bounds correct',np.allclose(acc['min'],d.min(0)) and np.allclose(acc['max'],d.max(0)))
    error=max(float(np.linalg.norm(d[ids]-d[ids[0]],axis=1).max()*1000) for ids in new_seams)
    metrics[f'target_{i}_new_seam_delta_mm']=error
    check(f'Target {i} new seams below 0.01 mm',error<.01)
max_weight_error=0
joints=after.arr(p['attributes']['JOINTS_0'])
for ids in new_seams:
    dense=[]
    for i in ids:
        d=np.zeros(52)
        for joint,weight in zip(joints[i],weights[i]):d[joint]+=weight
        dense.append(d)
    max_weight_error=max(max_weight_error,float(np.max(np.abs(np.array(dense)-dense[0]))))
metrics['new_seam_weight_error']=max_weight_error
check('New seam skin weights match',max_weight_error<1e-5)
metrics.update(glb_bytes=len(after.raw),triangles=sum(after.arr(p['indices']).size//3 for m in after.g['meshes'] for p in m['primitives']))
report={'checks_passed':sum(checks.values()),'checks_failed':sum(not x for x in checks.values()),'metrics':metrics,'checks':checks}
(root/'work/mouth32-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
assert all(checks.values())
