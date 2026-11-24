from kinematics27 import *
import json
candidate=Asset(root/'outputs/zachary_character_v27_candidate.glb');posed=world(node_data=candidate.g['nodes'])
p=candidate.prim('SM_Cloth_Hoodie');points=candidate.pos('SM_Cloth_Hoodie');tri=candidate.arr(p['indices']).reshape(-1,3)
report={}
for side in ['Right','Left']:
    elbow=posed[side+'ForeArm'][:3,3];axis=posed[side+'Hand'][:3,3]-posed[side+'Arm'][:3,3];axis/=np.linalg.norm(axis)
    signed=(points-elbow)@axis
    crossing=tri[(signed[tri].min(1)<0)&(signed[tri].max(1)>0)]
    segments=[]
    for face in crossing:
        hits=[]
        for a,b in [(0,1),(1,2),(2,0)]:
            i,j=face[a],face[b]
            if signed[i]*signed[j]<0:
                hits.append(points[i]+(points[j]-points[i])*signed[i]/(signed[i]-signed[j]))
        if len(hits)==2:segments.append(hits)
    segments=np.array(segments);unique,inv=np.unique(np.round(segments.reshape(-1,3),5),axis=0,return_inverse=True);edge=inv.reshape(-1,2);parent=list(range(len(unique)))
    def rep(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,b in edge:parent[rep(b)]=rep(a)
    groups={}
    for i,(a,b) in enumerate(edge):groups.setdefault(rep(a),[]).append(i)
    components=[]
    for ids in groups.values():
        lines=segments[ids];length=np.linalg.norm(lines[:,1]-lines[:,0],axis=1);center=np.sum(lines.mean(1)*length[:,None],axis=0)/length.sum()
        components.append({'segments':len(ids),'center':center.tolist(),'distance_mm':float(np.linalg.norm(center-elbow)*1000)})
    components.sort(key=lambda row:row['distance_mm']);report[side]={'old_pivot':elbow.tolist(),'cross_sections':components}
print(json.dumps(report,indent=2));(root/'work/elbow27-audit.json').write_text(json.dumps(report,indent=2))
