from glb_asset import Asset
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
asset=Asset(root/'outputs/zachary_character_v23_candidate.glb')
face=asset.pos('SM_Character_Face').copy()
tri=face[asset.arr(asset.prim('SM_Character_Face')['indices']).reshape(-1,3)]
def feather(lo,hi,x):
 t=np.clip((x-lo)/(hi-lo),0,1)
 return t*t*(3-2*t)
heights=np.linspace(1.568,1.605,149)
profiles={}
control_h=[1.568,1.575,1.581,1.586,1.590,1.594,1.597,1.599,1.601,1.603,1.605]
offset_mm=[-1.6,-.5,0,.1,0,-.5,-1.4,-2.8,-5.0,-8.5,-12]
for sign,width in [(-1,.09545),(1,.09297)]:
 observed=[]
 for h in heights:
  pieces=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   u,v=tri[:,i],tri[:,j]
   crossing=(u[:,1]-h)*(v[:,1]-h)<0
   u,v=u[crossing],v[crossing]
   pieces.append(u+((h-u[:,1])/(v[:,1]-u[:,1]))[:,None]*(v-u))
  p=np.concatenate(pieces);ear=p[(p[:,2]>-.040)&(p[:,2]<.006)&(p[:,0]*sign>.068)]
  observed.append(np.max(ear[:,0]*sign) if len(ear) else .080)
 target=width+np.interp(heights,control_h,np.array(offset_mm)*.001)
 correction=(target-np.array(observed))*feather(1.568,1.578,heights)*(1-feather(1.600,1.605,heights))
 profiles[sign]=np.clip(correction,-.001,.008)
for name in ['SM_Character_Face','SM_Character_Hair']:
 p=asset.pos(name);old=p.copy()
 x,y,z=old.T
 for sign in [-1,1]:
  side=x*sign
  w=feather(.072,.086,side)*feather(-.044,-.031,z)*(1-feather(-.006,.008,z))
  dx=np.interp(y,heights,profiles[sign],left=0,right=0)*w
  if name.endswith('Hair'):
   candidates=face[(face[:,0]*sign>.072)&(face[:,1]>1.55)&(face[:,1]<1.61)]
   for j in np.flatnonzero(w>0):
    distance=np.min(np.linalg.norm(candidates-old[j],axis=1))
    dx[j]*=1-feather(.001,.007,distance)
  final_limit=(.09545 if sign==-1 else .09297)+np.interp(y,control_h,np.array(offset_mm)*.001)
  corrected=side+dx
  trim=np.maximum(0,corrected-final_limit)*feather(1.576,1.582,y)*(1-feather(1.596,1.603,y))*w
  dx-=trim
  p[:,0]+=sign*dx
  p[:,2]+=.22*np.maximum(0,dx)
 # Relax isolated peaks on the outer rim across welded UV duplicates.
 if name.endswith('Face'):
  idx=asset.arr(asset.prim(name)['indices']).reshape(-1,3)
  _,inv=np.unique(np.round(old,6),axis=0,return_inverse=True)
  edges=np.unique(np.sort(inv[np.concatenate([idx[:,[0,1]],idx[:,[1,2]],idx[:,[2,0]]])],axis=1),axis=0)
  bound=set(map(tuple,np.round(asset.pos('SM_Character_Hair'),6)))
  free=np.array([tuple(v) not in bound for v in np.round(old,6)])
  weight=feather(.083,.092,abs(old[:,0]))*feather(1.574,1.582,old[:,1])*(1-feather(1.590,1.599,old[:,1]))*free
  for step in range(2):
   grouped=np.zeros((inv.max()+1,3));np.add.at(grouped,inv,p);grouped/=np.bincount(inv)[:,None]
   total=np.zeros_like(grouped); degree=np.zeros(len(grouped))
   for i,j in [(0,1),(1,0)]:np.add.at(total,edges[:,i],grouped[edges[:,j]]);np.add.at(degree,edges[:,i],1)
   p+=.15*weight[:,None]*(total/np.maximum(1,degree[:,None])-grouped)[inv]
 # Back off local edits that fold triangles, preserving UV seam duplicates.
 idx=asset.arr(asset.prim(name)['indices']).reshape(-1,3)
 before=old[idx];old_norm=np.cross(before[:,1]-before[:,0],before[:,2]-before[:,0])
 _,groups=np.unique(np.round(old,6),axis=0,return_inverse=True)
 for attempt in range(30):
  after=p[idx];new_norm=np.cross(after[:,1]-after[:,0],after[:,2]-after[:,0])
  area_old=np.linalg.norm(old_norm,axis=1);area_new=np.linalg.norm(new_norm,axis=1)
  cosine=(old_norm*new_norm).sum(1)/np.maximum(area_old*area_new,1e-20)
  bad=(cosine<.10)|(area_new<.20*area_old)
  if not bad.any():break
  affected=np.unique(groups[idx[bad]])
  selected=np.isin(groups,affected)
  p[selected]=old[selected]+.80*(p[selected]-old[selected])
 # Transport authored smooth normals through the changed triangle geometry.
 idx=asset.arr(asset.prim(name)['indices']).reshape(-1,3)
 def geometric(points):
  verts,inverse=np.unique(np.round(old,6),axis=0,return_inverse=True)
  v=points[idx];fn=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);s=np.zeros_like(verts)
  for c in range(3):np.add.at(s,inverse[idx[:,c]],fn)
  n=s[inverse];return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
 norm=asset.arr(asset.prim(name)['attributes']['NORMAL'])
 corrected=norm+geometric(p)-geometric(old)
 active=np.linalg.norm(p-old,axis=1)>1e-7
 norm[active]=corrected[active]/np.maximum(np.linalg.norm(corrected[active],axis=1)[:,None],1e-12)
# Lift the support locally over the restored cartilage while preserving hinge and lenses.
for pr in asset.g['meshes'][6]['primitives'][:2]:
 p=asset.arr(pr['attributes']['POSITION']); x,y,z=p.T
 w=feather(-.040,-.025,z)*(1-feather(-.003,.018,z))*feather(.070,.081,abs(x))
 p[:,1]+=.0000*w
 p[:,0]+=np.sign(x)*.0014*w
# At each depth slice, fit the innermost wire surface outside the head.
head_tris=np.concatenate([asset.pos(n)[asset.arr(asset.prim(n)['indices']).reshape(-1,3)] for n in ['SM_Character_Face','SM_Character_Hair']])
head_tris=head_tris[(head_tris[:,:,1].max(1)>1.57)&(head_tris[:,:,1].min(1)<1.62)]
o=head_tris[:,0];e=head_tris[:,1]-o;f=head_tris[:,2]-o
det=e[:,1]*f[:,2]-e[:,2]*f[:,1];den=np.where(abs(det)>1e-12,det,1)
def surface(h,z,side):
 dy=h-o[:,1];dz=z-o[:,2];u=(dy*f[:,2]-dz*f[:,1])/den;v=(e[:,1]*dz-e[:,2]*dy)/den
 ok=(abs(det)>1e-12)&(u>=0)&(v>=0)&(u+v<=1)
 return np.max(((o[:,0]+u*e[:,0]+v*f[:,0])*side)[ok],initial=0.)
parts=asset.g['meshes'][6]['primitives'][:2]
wire=np.concatenate([asset.arr(pr['attributes']['POSITION'])[asset.arr(pr['indices']).reshape(-1,3)] for pr in parts])
depth=np.linspace(-.040,.032,145)
for side in [-1,1]:
 needed=[]
 for z in depth:
  hits=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   u,v=wire[:,i],wire[:,j];cross=(u[:,2]-z)*(v[:,2]-z)<0
   u,v=u[cross],v[cross];hits.extend(u+((z-u[:,2])/(v[:,2]-u[:,2]))[:,None]*(v-u))
  hit=np.asarray(hits)
  if not len(hit): needed.append(0);continue
  hit=hit[hit[:,0]*side>.060]
  if not len(hit):needed.append(0);continue
  margin=max(surface(h+1.54,z,side) for h in np.linspace(hit[:,1].min(),hit[:,1].max(),7))+.0009-(hit[:,0]*side).min()
  needed.append(max(0,margin))
 padded=np.pad(needed,8,mode='edge')
 cap=np.maximum.reduce([padded[k:k+len(depth)] for k in range(17)])
 shift=np.convolve(np.pad(cap,4,mode='edge'),np.ones(9)/9,mode='valid')
 for pr in parts:
  p=asset.arr(pr['attributes']['POSITION']);mask=(p[:,0]*side>.060)&(p[:,2]<.032)
  p[mask,0]+=side*np.interp(p[mask,2],depth,shift)
 print('Local support correction mm',side,round(1000*max(shift),2))
asset.save(root/'outputs/zachary_character_v24_candidate.glb')
