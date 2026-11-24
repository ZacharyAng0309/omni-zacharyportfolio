"""Refine hand skinning with fitted bone envelopes and a seam-distance blend."""
from kinematics27 import *
import json, heapq
candidate=Asset(root/'outputs/zachary_character_v28_candidate.glb')
primitive=candidate.prim('SM_Character_Hands');points=candidate.pos('SM_Character_Hands')
joints=candidate.arr(primitive['attributes']['JOINTS_0']); weights=candidate.arr(primitive['attributes']['WEIGHTS_0'])
old_joints=joints.copy();old_weights=weights.copy()
triangles=candidate.arr(primitive['indices']).reshape(-1,3)
skin=candidate.g['skins'][0]; names=[candidate.g['nodes'][i]['name'] for i in skin['joints']]
transforms=world(node_data=candidate.g['nodes'])
changes=json.loads((root/'work/finger28-changes.json').read_text())
unique,inverse=np.unique(np.round(points,6),axis=0,return_inverse=True)
edges=np.unique(np.sort(np.concatenate([inverse[triangles[:,[0,1]]],inverse[triangles[:,[1,2]]],inverse[triangles[:,[2,0]]]]),axis=1),axis=0)
graph=[{} for _ in unique]
for a,b in edges:
    if a==b:continue
    d=np.linalg.norm(unique[a]-unique[b]);graph[a][b]=d;graph[b][a]=d
hoodie=set(map(tuple,np.round(candidate.pos('SM_Cloth_Hoodie'),6)))
seam=[i for i,p in enumerate(unique) if tuple(p) in hoodie]
distance=np.full(len(unique),np.inf);queue=[]
for i in seam:distance[i]=0;heapq.heappush(queue,(0,i))
while queue:
    d,i=heapq.heappop(queue)
    if d!=distance[i]:continue
    for j,length in graph[i].items():
        if d+length<distance[j]:distance[j]=d+length;heapq.heappush(queue,(d+length,j))
blend=np.clip(distance[inverse]/.045,0,1);blend=blend*blend*(3-2*blend)
assert np.all(np.isfinite(distance))
envelopes=np.zeros((len(points),len(names)))
for side in ['Right','Left']:
    hand=side+'Hand';wrist=transforms[hand][:3,3]
    roots=np.array([transforms[hand+finger+'1'][:3,3] for finger in ['Index','Middle','Ring','Pinky']])
    segments=[(hand,wrist,roots.mean(axis=0))]
    for finger in ['Thumb','Index','Middle','Ring','Pinky']:
        for number in [1,2,3]:
            name=hand+finger+str(number);a=transforms[name][:3,3]
            b=transforms[hand+finger+str(number+1)][:3,3] if number<3 else np.array(changes['finger_tips_m'][hand+finger])
            segments.append((name,a,b))
    # Use the inherited side's rig assignment to exclude the opposite hand.
    side_indices=[i for i,name in enumerate(names) if name.startswith(side)]
    side_weight=np.sum(old_weights*np.isin(old_joints,side_indices),axis=1)
    for name,a,b in segments:
        delta=b-a;t=np.clip(((points-a)@delta)/np.dot(delta,delta),0,1)
        closest=a+t[:,None]*delta
        d2=np.sum((points-closest)**2,axis=1)
        envelopes[:,names.index(name)]=side_weight/(d2+.006**2)**3
envelopes/=envelopes.sum(axis=1,keepdims=True)
original=np.zeros_like(envelopes)
for i in range(4):original[np.arange(len(points)),old_joints[:,i]]+=old_weights[:,i]
merged=original*(1-blend[:,None])+envelopes*blend[:,None]
for index,row in enumerate(merged):
    if blend[index]==0:continue
    selected=np.argsort(row)[-4:][::-1]
    values=row[selected];values/=values.sum()
    joints[index]=selected;weights[index]=values
assert np.max(abs(weights.sum(axis=1)-1))<1e-6
seam_vertices=np.isin(inverse,seam)
assert np.array_equal(joints[seam_vertices],old_joints[seam_vertices])
assert np.array_equal(weights[seam_vertices],old_weights[seam_vertices])
candidate.save(root/'outputs/zachary_character_v28_candidate.glb')
report={'method':'inverse-distance bone envelopes; smooth 45 mm geodesic blend from cuff seam',
        'vertices_reweighted':int(np.sum(np.any(weights!=old_weights,axis=1)|np.any(joints!=old_joints,axis=1))),
        'seam_vertices_preserved':int(seam_vertices.sum()),'max_influences':4,'weight_sum_max_error':float(np.max(abs(weights.sum(axis=1)-1)))}
(root/'work/finger28-weights.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
