"""Small proportional crown-part sculpt; retain all boundary and rig data."""
from pathlib import Path
import numpy as np,json
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];a=Asset(root/'outputs/zachary_character_v37_candidate.glb');p=a.prim('SM_Character_Hair')
pos=a.arr(p['attributes']['POSITION']);old=pos.copy();tri=a.arr(p['indices']).reshape(-1,3)
unique,inv=np.unique(np.round(old,6),axis=0,return_inverse=True);lt=inv[tri]
def smooth(v):
 w=np.clip(v,0,1);return w*w*(3-2*w)
# Artist-placed proportional brush for the part, not a replacement anatomical surface.
radial=np.sqrt(((unique[:,0]+.014)/.022)**2+((unique[:,2]-.015)/.075)**2)
w=smooth(1-radial)*smooth((unique[:,1]-1.691)/.035)
facekeys=set(map(tuple,np.round(a.pos('SM_Character_Face'),6)))
edges,counts=np.unique(np.sort(np.concatenate([lt[:,[0,1]],lt[:,[1,2]],lt[:,[2,0]]]),axis=1),axis=0,return_counts=True)
boundary=np.unique(edges[counts==1]);w[boundary]=0
shared=np.array([tuple(v) in facekeys for v in unique]);w[shared]=0
delta=np.zeros_like(unique);delta[:,1]=-.0055*w
new=old+delta[inv];oc=np.cross(old[tri[:,1]]-old[tri[:,0]],old[tri[:,2]]-old[tri[:,0]]);nc=np.cross(new[tri[:,1]]-new[tri[:,0]],new[tri[:,2]]-new[tri[:,0]])
cos=np.sum(oc*nc,axis=1)/np.maximum(np.linalg.norm(oc,axis=1)*np.linalg.norm(nc,axis=1),1e-15)
ratio=np.linalg.norm(nc,axis=1)/np.maximum(np.linalg.norm(oc,axis=1),1e-15)
assert cos.min()>.8 and ratio.min()>.65
def normals(cross):
 n=np.zeros_like(unique)
 for i in range(3):np.add.at(n,lt[:,i],cross)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);return n[inv]
base=a.arr(p['attributes']['NORMAL']);moved=np.linalg.norm(delta[inv],axis=1)>1e-8
transported=base+normals(nc)-normals(oc);transported/=np.maximum(np.linalg.norm(transported,axis=1)[:,None],1e-12)
base[moved]=transported[moved];pos[:]=new
a.save(root/'work/hair38-shape.glb')
report={'affected_vertex_copies':int(moved.sum()),'max_displacement_mm':float(np.linalg.norm(new-old,axis=1).max()*1000),'minimum_triangle_orientation_cosine':float(cos.min()),'minimum_area_ratio':float(ratio.min()),'shared_face_boundary_movement_mm':float(np.linalg.norm(delta[shared],axis=1).max()*1000),'all_boundary_movement_mm':float(np.linalg.norm(delta[boundary],axis=1).max()*1000)}
(root/'work/hair38-shape.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
