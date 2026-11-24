"""Tune the v36 eye assembly without rebuilding or rebaking the surrounding face."""
import bpy,sys,json,numpy as np
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v36_candidate.glb');rings=json.loads((root/'work/eye36-rings.json').read_text())
def normal(x,t):
 n=np.zeros_like(x);c=np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]])
 for k in range(3):np.add.at(n,t[:,k],c)
 return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
def transport(prim,old,new):
 t=a.arr(prim['indices']).reshape(-1,3);norm=a.arr(prim['attributes']['NORMAL']);change=normal(new,t)-normal(old,t);active=np.linalg.norm(new-old,axis=1)>1e-9
 result=norm+change;result/=np.maximum(np.linalg.norm(result,axis=1)[:,None],1e-12);norm[active]=result[active]
def smooth(lo,hi,x):
 t=np.clip((x-lo)/(hi-lo),0,1);return t*t*(3-2*t)
def placement(x):
 # Constant translation over the moving lids, fading outside the orbit.
 distance=np.minimum(abs(x[:,0]-.034),abs(x[:,0]+.034))
 w=(1-smooth(.029,.037,distance))*(1-smooth(.023,.038,abs(x[:,1]-1.598)))*smooth(.045,.067,x[:,2])
 return w
before={};changed={}
for name in ['SM_Character_Face','SM_Character_Hair','SM_Character_Eyelids','SM_Character_EyeLeft','SM_Character_EyeRight']:
 before[name]=a.pos(name).copy()
p=a.prim('SM_Character_Eyelids');x=a.arr(p['attributes']['POSITION']);base=x.copy();target_arrays=[a.arr(t['POSITION']) for t in p['targets']];original_targets=[t.copy() for t in target_arrays]
for side in rings:
 sign=side['sign'];k=4 if sign>0 else 5;center=np.array([sign*.034,1.598]);angles=np.arange(32)*2*np.pi/32
 for level,ring in enumerate(side['rings']):
  amount=[0,.45,1,1][level];old=x[ring].copy();dx=.0008*np.cos(angles)*amount
  # Slight outer-corner lift, with a fuller lower arc as in the portrait.
  dy=amount*(.0008*sign*np.cos(angles)+np.where(np.sin(angles)>0,.0005,.0011)*np.sin(angles))
  x[ring,0]+=dx;x[ring,1]+=dy
  def globe(q):
   xx=q[:,0]-center[0];yy=q[:,1]-center[1];return side['zcenter']+.0105*np.sqrt(np.maximum(.001,1-(xx/.017)**2-(yy/.012)**2))-sign*.22*xx
  x[ring,2]+=globe(x[ring])-globe(old)
  if level==1:x[ring,2]-=.0002*np.maximum(np.sin(angles),0)**2
  # Preserve the established closed target exactly after changing neutral lids.
  target_arrays[k][ring]=(base[ring]+original_targets[k][ring])-x[ring]
lid_shape=x-base
for name in before:
 prim=a.prim(name);points=a.arr(prim['attributes']['POSITION']);old=points.copy();w=placement(before[name])
 if name.startswith('SM_Character_Eye') and name!='SM_Character_Eyelids':w[:]=1
 points[:,1]-=.0016*w
 transport(prim,before[name],points)
 changed[name]={'placement_max_mm':float((.0016*w).max()*1000),'changed_copies':int(np.sum(np.linalg.norm(points-before[name],axis=1)>1e-7))}
# Refit iris/pupil rings, preserving the globe's outer silhouette and skin fit.
for side in rings:
 name='SM_Character_EyeLeft' if side['sign']>0 else 'SM_Character_EyeRight';prim=a.prim(name);points=a.pos(name);old=points.copy();color=a.arr(prim['attributes']['COLOR_0']);center=np.array([side['sign']*.034,1.5964]);angles=np.arange(32)*2*np.pi/32
 for ring,(radius,tint) in enumerate([(.0020,(.0015,.0010,.0007)),(.0041,(.027,.011,.004)),(.0058,(.037,.017,.007)),(.0060,(.011,.006,.003))]):
  ids=np.arange(1+ring*32,1+(ring+1)*32);points[ids,:2]=center+radius*np.column_stack([np.cos(angles),np.sin(angles)])
  xx=points[ids,0]-center[0];yy=points[ids,1]-center[1];points[ids,2]=side['zcenter']+.0105*np.sqrt(1-(xx/.017)**2-(yy/.012)**2)-side['sign']*.22*xx-.0005
  variation=1 if ring in [0,3] else (.82+.18*np.sin(angles*13+.6)**2)[:,None];color[ids]=np.array(tint)*variation
 transport(prim,old,points)
 mat=a.g['materials'][prim['material']];mat['pbrMetallicRoughness']['roughnessFactor']=.14;mat['extensions']['KHR_materials_specular']['specularFactor']=.10
# Refresh lid normal targets for the adjusted neutral and preserved closed state.
prim=a.prim('SM_Character_Eyelids');points=a.pos('SM_Character_Eyelids');tri=a.arr(prim['indices']).reshape(-1,3);n0=normal(points,tri);boundary=[i for side in rings for i in side['boundary_indices']]
for target in prim['targets']:
 delta=a.arr(target['POSITION']);dn=normal(points+delta,tri)-n0;dn[boundary]=0;a.arr(target['NORMAL'])[:]=dn
 for sem,index in target.items():
  arr=a.arr(index);a.g['accessors'][index].update(min=arr.min(0).tolist(),max=arr.max(0).tolist())
a.save(root/'work/zachary_character_v37_tuning.glb')
(root/'work/tune37-changes.json').write_text(json.dumps({'source':'v36','placement_y_mm':-1.6,'pupil_radius_before_after_mm':[2.5,2.0],'iris_radius_before_after_mm':[5.3,5.8],'new_images':0,'changes':changed},indent=2));print('TUNED',changed)
