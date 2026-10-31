from glb_asset import *
from collections import defaultdict
r=Path(__file__).resolve().parents[1]
a=Asset(r/'outputs/zachary_character_v22_candidate.glb'); b=Asset(r'D:\omni-workstation\projects\ZacharyPortfolio\public\models\zachary_textured_v19.glb')
def smooth(lo,hi,x):
 t=np.clip((x-lo)/(hi-lo),0,1);return t*t*(3-2*t)
def attrs(s):
 ps=[m['primitives'][0] for m in s.g['meshes'][:6]]
 return [[s.arr(p['attributes'][k]) for p in ps] for k in ['POSITION','TEXCOORD_0','NORMAL']]
ps,us,ns=attrs(a); qs,vs,ms=attrs(b)
q,v,m=map(np.concatenate,[qs,vs,ms]);lut=defaultdict(list)
for i,uv in enumerate(v):lut[tuple(uv)].append(i)
changes=defaultdict(list)
for pp,uu,nn in zip(ps[:2],us[:2],ns[:2]):
 for xyz,uv,n in zip(pp,uu,nn):
  x,y,z=xyz;w=smooth(.055,.076,abs(x))*smooth(1.528,1.552,y)*(1-smooth(1.608,1.635,y))*smooth(-.055,-.038,z)*(1-smooth(.051,.078,z))
  if w and tuple(uv) in lut:
   ids=lut[tuple(uv)]; i=ids[np.argmin(np.linalg.norm(q[ids]-xyz,axis=1))]
   d=q[i]-xyz;w*=.72*min(1,.023/max(1e-9,np.linalg.norm(d)))
   changes[tuple(xyz)].append((d*w,(m[i]-n)*w))
for pp,nn in zip(ps[:2],ns[:2]):
 for i,xyz in enumerate(pp):
  items=changes.get(tuple(xyz))
  if items:
   d,dn=np.mean(items,axis=0);pp[i]+=d;nn[i]+=dn;nn[i]/=max(np.linalg.norm(nn[i]),1e-12)
# Fit the accessory to cross-sections of the restored face + hair.
tris=np.concatenate([a.pos(name)[a.arr(a.prim(name)['indices']).reshape(-1,3)] for name in ['SM_Character_Face','SM_Character_Hair']])
o=tris[:,0];e=tris[:,1]-o;f=tris[:,2]-o;det=e[:,1]*f[:,2]-e[:,2]*f[:,1];den=np.where(abs(det)>1e-12,det,1)
def extent(y,z,side):
 dy=y-o[:,1];dz=z-o[:,2];u=(dy*f[:,2]-dz*f[:,1])/den;v=(e[:,1]*dz-e[:,2]*dy)/den
 ok=(abs(det)>1e-12)&(u>=0)&(v>=0)&(u+v<=1)
 return max(((o[:,0]+u*e[:,0]+v*f[:,0])*side)[ok],default=0.)
zs=np.linspace(-.042,.100,72)
t=smooth(-.015,.0755,zs);hook=np.clip((-.016-zs)/.0225,0,1)
oldcx=.0666*t+(.0818-.0035*hook**1.5)*(1-t)
oldcy=.0568*t+.0578*(1-t)-.0125*hook**1.65
dy=.0035*(1-smooth(-.012,.067,zs))
for side in [-1,1]:
 target=[]
 for z,cy in zip(zs,oldcy+dy):
  surf=max(extent(1.54+cy+oy,z,side) for oy in [-.0018,0,.0018])
  target.append(surf+.0029+.0038*smooth(-.003,.032,z))
 cx=np.convolve(np.pad(target,2,mode='edge'),np.array([1,2,3,2,1])/9,mode='valid')
 dx=(cx-oldcx)*(1-smooth(.060,.077,zs))
 for pr in a.g['meshes'][6]['primitives'][:2]:
  pp=a.arr(pr['attributes']['POSITION']);nn=a.arr(pr['attributes']['NORMAL'])
  take=(pp[:,0]*side>.060)&(pp[:,2]<.077)
  z=pp[take,2];pp[take,0]+=side*np.interp(z,zs,dx);pp[take,1]+=np.interp(z,zs,dy)
  nn[take,2]-=side*np.interp(z,zs,np.gradient(dx,zs))*nn[take,0]+np.interp(z,zs,np.gradient(dy,zs))*nn[take,1];nn[take]/=np.maximum(np.linalg.norm(nn[take],axis=1)[:,None],1e-12)
a.save(r/'outputs/zachary_character_v23_candidate.glb')
print(len(changes),'matched position clusters; maximum restorative motion mm',max(np.linalg.norm(np.mean(v,axis=0)[0]) for v in changes.values())*1000)
