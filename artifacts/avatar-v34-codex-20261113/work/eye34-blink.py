"""Small constrained blink corrections prevent two outer-corner triangle inversions."""
import numpy as np,json
from pathlib import Path
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];a=Asset(root/'outputs/zachary_character_v34_candidate.glb');p=a.prim('SM_Character_Face');x=a.pos('SM_Character_Face').copy();tri=a.arr(p['indices']).reshape(-1,3).copy();patch=np.load(root/'work/eye34-baked-data.npz')['patched']
_,ids,w=np.unique(np.rint(x.astype(float)*1e6).astype('i8'),axis=0,return_index=True,return_inverse=True);t=w[tri];points=x[ids].astype(float)*1000
coeff=np.column_stack([points[t[:,2],0]-points[t[:,1],0],points[t[:,0],0]-points[t[:,2],0],points[t[:,1],0]-points[t[:,0],0]])
rest_area=np.sum(coeff*points[t,1],axis=1);reports=[]
brow=a.arr(p['targets'][6]['POSITION'])[ids].astype(float)*1000
brow_area=np.sum(coeff*brow[t,1],axis=1)
for target in [4,5]:
 index=p['targets'][target]['POSITION'];delta=a.arr(index);d=delta[ids].astype(float)*1000;area=np.sum(coeff*(points[t,1]+d[t,1]),axis=1);worst_area=area+np.minimum(brow_area,0);bad=np.where(patch&(worst_area<.00005))[0]
 if not len(bad):continue
 variables=set(int(i) for i in t[bad].ravel())
 original=set(variables)
 for face in t:
  if any(int(i) in original for i in face):variables.update(int(i) for i in face)
 variables=sorted(i for i in variables if abs(d[i,1])>1e-7);lookup={v:i for i,v in enumerate(variables)}
 selected=np.array([any(int(i) in lookup for i in face) for face in t])&(rest_area>1e-6)
 matrix=np.zeros((sum(selected),len(variables)))
 for row,(face,co) in enumerate(zip(t[selected],coeff[selected])):
  for i,c in zip(face,co):
   if int(i) in lookup:matrix[row,lookup[int(i)]]+=c
 rhs=np.maximum(rest_area[selected]*.01,.00005)-worst_area[selected]
 # Alternating projections onto the local linear area constraints and bounds.
 correction=np.zeros(len(variables))
 for iteration in range(20000):
  violation=rhs-matrix@correction
  if violation.max()<1e-9:break
  row=int(np.argmax(violation));normal=matrix[row]
  assert normal@normal>1e-15
  correction+=normal*(violation[row]+1e-8)/(normal@normal)
  correction=np.clip(correction,-.5,.5)
 assert (rhs-matrix@correction).max()<1e-7,'Area constraints did not converge'
 for geo,value in zip(variables,correction):delta[w==geo,1]+=value/1000
 a.g['accessors'][index].update(min=delta.min(0).tolist(),max=delta.max(0).tolist())
 final=x+delta;cross=np.cross(final[tri[:,1]]-final[tri[:,0]],final[tri[:,2]]-final[tri[:,0]])
 assert np.all(cross[patch,2]>0)
 reports.append({'target':target,'original_inverted_patch_triangles':len(bad),'final_inverted_patch_triangles':0,'max_adjustment_mm':float(abs(correction).max()),'adjusted_geometric_vertices':int(sum(abs(correction)>1e-6))})
a.save(root/'outputs/zachary_character_v34_candidate.glb');(root/'work/eye34-blink-changes.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
