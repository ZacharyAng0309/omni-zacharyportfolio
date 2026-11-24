"""Fit finger pivots to surface midlines and orient local flexion axes.

Joint spacing is an authored anatomical approximation. Cross-hand ray pairs
locate the mid-surface at those landmarks. Vertex arrays and weights are intact.
"""
from kinematics27 import *
import json
candidate=Asset(root/'outputs/zachary_character_v27_candidate.glb')
old_world=world(node_data=candidate.g['nodes'])
points=candidate.pos('SM_Character_Hands')
triangles=candidate.arr(candidate.prim('SM_Character_Hands')['indices']).reshape(-1,3)
skin=candidate.g['skins'][0]
bind=candidate.arr(skin['inverseBindMatrices'])
# MCP, PIP, DIP and terminal points, following measured finger contours.
landmarks={
 'Index':[(.825,.091),(.794,.098),(.774,.102),(.763,.103)],
 'Middle':[(.825,.070),(.791,.073),(.767,.077),(.751,.078)],
 'Ring':[(.825,.047),(.791,.050),(.767,.051),(.752,.051)],
 'Pinky':[(.825,.023),(.801,.0245),(.784,.024),(.771,.023)],
 'Thumb':[(.850,.098),(.835,.111),(.823,.120),(.816,.124)]}

def mid_surface(side,y,z):
    sign=-1 if side=='Right' else 1
    mesh=points[triangles]
    mesh=mesh[np.mean(mesh[:,:,0],axis=1)*sign>0]
    hits=[]
    for triangle in mesh:
        yz=triangle[:,1:]
        matrix=np.column_stack([yz[1]-yz[0],yz[2]-yz[0]])
        if abs(np.linalg.det(matrix))<1e-12: continue
        u,v=np.linalg.solve(matrix,np.array([y,z])-yz[0])
        if u>=-1e-6 and v>=-1e-6 and u+v<=1+1e-6:
            hits.append(float(triangle[0,0]+u*(triangle[1,0]-triangle[0,0])+v*(triangle[2,0]-triangle[0,0])))
    hits=sorted(set(round(x,7) for x in hits))
    assert len(hits)>=2,(side,y,z,hits)
    return np.array([(hits[0]+hits[-1])/2,y,z]),hits

def quaternion(matrix):
    # Eigenvector form, robust near 180-degree rotations. Return glTF xyzw.
    m=matrix
    K=np.array([[m[0,0]-m[1,1]-m[2,2],m[0,1]+m[1,0],m[0,2]+m[2,0],m[2,1]-m[1,2]],
                [m[0,1]+m[1,0],m[1,1]-m[0,0]-m[2,2],m[1,2]+m[2,1],m[0,2]-m[2,0]],
                [m[0,2]+m[2,0],m[1,2]+m[2,1],m[2,2]-m[0,0]-m[1,1],m[1,0]-m[0,1]],
                [m[2,1]-m[1,2],m[0,2]-m[2,0],m[1,0]-m[0,1],m.trace()]])/3
    _,vectors=np.linalg.eigh(K); q=vectors[:,-1]
    if q[3]<0: q=-q
    assert np.max(abs(rotation_quaternion(q)-matrix))<1e-6
    return q.tolist()

new_world={name:matrix.copy() for name,matrix in old_world.items()}
measurements={}; terminal={}
for side in ['Right','Left']:
    for finger,samples in landmarks.items():
        positions=[]
        for y,z in samples:
            center,hits=mid_surface(side,y,z); positions.append(center)
        terminal[side+'Hand'+finger]=positions[-1].tolist()
        for index in range(3):
            name=side+'Hand'+finger+str(index+1)
            center=positions[index]
            along=positions[index+1]-center; along/=np.linalg.norm(along)
            palmward=np.array([1.,0,0]) if side=='Right' else np.array([-1.,0,0])
            palmward-=along*np.dot(palmward,along); palmward/=np.linalg.norm(palmward)
            across=np.cross(along,palmward); across/=np.linalg.norm(across)
            orientation=np.column_stack([across,along,palmward])
            new_world[name][:3,:3]=orientation
            new_world[name][:3,3]=center
            measurements[name]={'old_position_m':old_world[name][:3,3].tolist(),'new_position_m':center.tolist(),
                                'offset_corrected_mm':float(np.linalg.norm(center-old_world[name][:3,3])*1000)}

for name in measurements:
    node_index=by_name[name]; parent_name=nodes[parents[node_index]]['name']
    local=np.linalg.inv(new_world[parent_name])@new_world[name]
    node=candidate.g['nodes'][node_index]
    node['translation']=local[:3,3].tolist(); node['rotation']=quaternion(local[:3,:3])
    ji=skin['joints'].index(node_index)
    old_bind=bind[ji].reshape(4,4).T.copy()
    bind[ji]=(np.linalg.inv(new_world[name])@old_world[name]@old_bind).T.reshape(-1)
candidate.save(root/'outputs/zachary_character_v28_candidate.glb')
report={'method':'surface midlines at authored joint landmarks; local +X flexion toward palm',
        'changes':measurements,'finger_tips_m':terminal,
        'pose_contract':'Multiply each finger rest quaternion by local X-axis curl quaternion. Do not overwrite absolute Euler X.'}
(root/'work/finger28-changes.json').write_text(json.dumps(report,indent=2))
print('Corrected',len(measurements),'finger pivots. Offset range mm:',min(x['offset_corrected_mm'] for x in measurements.values()),max(x['offset_corrected_mm'] for x in measurements.values()))
