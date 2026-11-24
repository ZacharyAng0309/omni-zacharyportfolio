"""Locally relax uneven palm geometry and smooth existing hand weight fields."""
from kinematics27 import *
import json,heapq
candidate=Asset(root/'outputs/zachary_character_v28_candidate.glb')
p=candidate.prim('SM_Character_Hands');points=candidate.pos('SM_Character_Hands');initial=points.copy()
triangles=candidate.arr(p['indices']).reshape(-1,3)
joints=candidate.arr(p['attributes']['JOINTS_0']);weights=candidate.arr(p['attributes']['WEIGHTS_0'])
original_joints=joints.copy();original_weights=weights.copy()
normals=candidate.arr(p['attributes']['NORMAL']);original_normals=normals.copy()
unique,first,inverse=np.unique(np.round(points,6),axis=0,return_index=True,return_inverse=True)
unique=points[first].astype(float).copy();initial_unique=unique.copy()
faces=inverse[triangles]
edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
neighbors=[set() for _ in unique]
for a,b in edges:neighbors[a].add(b);neighbors[b].add(a)
hoodie=set(map(tuple,np.rint(candidate.pos('SM_Cloth_Hoodie').astype(float)*1e6).astype(np.int64)))
seam=np.array([i for i,v in enumerate(unique) if tuple(np.rint(v*1e6).astype(np.int64)) in hoodie],dtype=int)
assert len(seam)>=90, 'The cuff seam must be found before refinement'
dist=np.full(len(unique),np.inf);queue=[]
for i in seam:dist[i]=0;heapq.heappush(queue,(0,i))
while queue:
    d,i=heapq.heappop(queue)
    if d!=dist[i]:continue
    for j in neighbors[i]:
        length=np.linalg.norm(unique[i]-unique[j])
        if d+length<dist[j]:dist[j]=d+length;heapq.heappush(queue,(d+length,j))
names=[candidate.g['nodes'][i]['name'] for i in candidate.g['skins'][0]['joints']]
dense=np.zeros((len(points),len(names)))
for k in range(4):dense[np.arange(len(points)),joints[:,k]]+=weights[:,k]
fields=dense[first].copy()
proximal=[i for i,name in enumerate(names) if name.endswith('Hand') or ('Hand' in name and name[-1:]=='1')]
palm=np.clip((fields[:,proximal].sum(axis=1)-.4)/.55,0,1)
cuff=np.clip((dist-.012)/.025,0,1);cuff=cuff*cuff*(3-2*cuff)
influence=palm*cuff

# Local Laplacian relaxation. Cuff attachment and distal finger surface stay fixed.
for iteration in range(5):
    average=np.array([unique[list(row)].mean(axis=0) for row in neighbors])
    trial=unique+.40*influence[:,None]*(average-unique)
    delta=trial-initial_unique;length=np.linalg.norm(delta,axis=1)
    delta*=np.minimum(1,.0015/np.maximum(length,1e-12))[:,None]
    unique=initial_unique+delta
points[:]=unique[inverse]
# The weighted adjacency smoothing follows mesh connectivity, not spatial boxes.
for iteration in range(5):
    average=np.array([fields[list(row)].mean(axis=0) for row in neighbors])
    fields+=.35*influence[:,None]*(average-fields)
fields=np.maximum(fields,0);fields/=fields.sum(axis=1,keepdims=True)
for vertex,row in enumerate(fields[inverse]):
    if influence[inverse[vertex]]==0:continue
    chosen=np.argsort(row)[-4:][::-1];values=row[chosen];values/=values.sum()
    joints[vertex]=chosen;weights[vertex]=values

# Recompute geometric normals only on the changed patch and its immediate ring.
affected=set(np.flatnonzero(np.linalg.norm(unique-initial_unique,axis=1)>1e-8))
for i in list(affected):affected.update(neighbors[i])
face_normals=np.cross(unique[faces[:,1]]-unique[faces[:,0]],unique[faces[:,2]]-unique[faces[:,0]])
new_normals=np.zeros_like(unique)
for k in range(3):np.add.at(new_normals,faces[:,k],face_normals)
new_normals/=np.maximum(np.linalg.norm(new_normals,axis=1)[:,None],1e-15)
for vertex,uid in enumerate(inverse):
    if uid in affected and uid not in seam:normals[vertex]=new_normals[uid]
seam_vertices=np.isin(inverse,seam)
assert int(seam_vertices.sum())==101
assert np.array_equal(points[seam_vertices],initial[seam_vertices])
assert np.array_equal(joints[seam_vertices],original_joints[seam_vertices])
assert np.array_equal(weights[seam_vertices],original_weights[seam_vertices])
candidate.save(root/'outputs/zachary_character_v29_candidate.glb')
displacement=np.linalg.norm(points-initial,axis=1)*1000
old_cross=np.cross(initial[triangles[:,1]]-initial[triangles[:,0]],initial[triangles[:,2]]-initial[triangles[:,0]])
new_cross=np.cross(points[triangles[:,1]]-points[triangles[:,0]],points[triangles[:,2]]-points[triangles[:,0]])
flips=np.sum(np.einsum('ij,ij->i',old_cross,new_cross)<=0)
assert flips==0
report={'method':'localized Laplacian relaxation and adjacency weight diffusion, selected by existing proximal hand weights and geodesic cuff distance',
 'moved_vertices':int(sum(displacement>1e-5)),'max_displacement_mm':float(displacement.max()),
 'reweighted_vertices':int(sum(np.any(weights!=original_weights,axis=1)|np.any(joints!=original_joints,axis=1))),
 'seam_vertices_preserved':int(seam_vertices.sum()),'triangle_flips':int(flips),'iterations':5}
(root/'work/hand29-changes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
