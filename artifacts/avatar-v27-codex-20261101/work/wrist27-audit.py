from kinematics27 import *
primitive=asset.prim('SM_Character_Hands');points=asset.pos('SM_Character_Hands'); triangles=asset.arr(primitive['indices']).reshape(-1,3)
unique,inverse=np.unique(np.round(points,6),axis=0,return_inverse=True); parent=list(range(len(unique)))
def rep(i):
    while parent[i]!=i:
        parent[i]=parent[parent[i]];i=parent[i]
    return i
for a,b,c in inverse[triangles]: parent[rep(b)]=rep(a);parent[rep(c)]=rep(a)
groups={}
for index in range(len(unique)):groups.setdefault(rep(index),[]).append(index)
hoodie=set(map(tuple,np.round(asset.pos('SM_Cloth_Hoodie'),6)))
for indices in sorted(groups.values(),key=len,reverse=True):
    seam=np.array([unique[i] for i in indices if tuple(unique[i]) in hoodie])
    if len(seam):
        center=seam.mean(0);side='Left' if center[0]>0 else 'Right';pivot=rest[side+'Hand'][:3,3]
        print(side,'component vertices',len(indices),'seam vertices',len(seam),'seam center',center,'joint',pivot,'offset mm',np.linalg.norm(center-pivot)*1000)
