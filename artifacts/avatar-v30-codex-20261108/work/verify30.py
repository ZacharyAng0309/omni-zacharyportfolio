from kinematics27 import *
import json
before=Asset(root/'outputs/zachary_character_v29_candidate.glb');after=Asset(root/'outputs/zachary_character_v30_candidate.glb')
checks={}
def check(name,value):checks[name]=bool(value);assert value,name
for field in ['nodes','meshes','materials','skins','images','textures','samplers','scenes']:
    check(field+' preserved',before.g[field]==after.g[field])
primitive=before.prim('SM_Character_Hands');attrs=primitive['attributes'];allowed=set(attrs.values())|{primitive['indices']}
for i in range(len(before.g['accessors'])):
    if i not in allowed:check(f'non-hand accessor {i} preserved',np.array_equal(before.arr(i),after.arr(i)))
for semantic,index in attrs.items():
    check('original hand '+semantic+' and vertex order preserved',np.array_equal(before.arr(index),after.arr(index)[:len(before.arr(index))]))
for i,image in enumerate(before.g['images']):
    view=before.g['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0);length=view['byteLength']
    check(f'image {i} bytes preserved',before.bin[offset:offset+length]==after.bin[offset:offset+length])
    check(f'image {i} below 100 KB',length<100000)
def topology(asset):
    p=asset.prim('SM_Character_Hands');v=asset.pos('SM_Character_Hands');t=asset.arr(p['indices']).reshape(-1,3)
    quantized=np.rint(v.astype(float)*1e6).astype(np.int64)
    u,inv=np.unique(quantized,axis=0,return_inverse=True);f=inv[t]
    edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);e,c=np.unique(edges,axis=0,return_counts=True)
    boundary={tuple(sorted((tuple(u[a]),tuple(u[b])))) for a,b in e[c==1]}
    graph={int(i):set() for i in np.unique(f)}
    for a,b in e:graph[int(a)].add(int(b));graph[int(b)].add(int(a))
    visited=set();components=0
    for seed in graph:
        if seed in visited:continue
        components+=1;todo=[seed]
        while todo:
            i=todo.pop()
            if i in visited:continue
            visited.add(i);todo.extend(graph[i]-visited)
    return {'boundary':boundary,'max_edge_faces':int(c.max()),'components':components,'euler':len(np.unique(f))-len(e)+len(f),
            'vertices':v,'triangles':t,'active_vertices':len(np.unique(t))}
oldtop=topology(before);newtop=topology(after)
check('cuff boundary edges identical',newtop['boundary']==oldtop['boundary'])
check('exactly 95 existing cuff boundary edges',len(newtop['boundary'])==95)
check('no non-manifold hand edges',newtop['max_edge_faces']==2)
check('two connected hands retained',newtop['components']==oldtop['components']==2)
check('two handles from fused webs removed',oldtop['euler']==-2 and newtop['euler']==2)
v=newtop['vertices'];t=newtop['triangles']
cross=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
check('no degenerate hand faces',np.min(np.linalg.norm(cross,axis=1))>1e-12)
check('indices in range',t.min()>=0 and t.max()<len(v))
check('no repeated-index triangles',np.all(np.diff(np.sort(t,axis=1),axis=1)>0))
normal=after.arr(attrs['NORMAL']);weights=after.arr(attrs['WEIGHTS_0']);joints=after.arr(attrs['JOINTS_0'])
check('all hand attributes finite',all(np.all(np.isfinite(after.arr(index))) for index in attrs.values()))
check('normals normalized',np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-5)
check('weights normalized',np.max(abs(weights.sum(axis=1)-1))<1e-6)
check('weights nonnegative',weights.min()>=0)
check('at most four influences',weights.shape[1]==4)
check('valid joint indices',joints.max()<len(after.g['skins'][0]['joints']))
check('UVs within source range',after.arr(attrs['TEXCOORD_0']).min()>=0 and after.arr(attrs['TEXCOORD_0']).max()<=1)
def hits(asset,y):
    z=.064-.16*(y-.775);vv=asset.pos('SM_Character_Hands').astype(float);tt=asset.arr(asset.prim('SM_Character_Hands')['indices']).reshape(-1,3)
    output=[]
    for triangle in vv[tt]:
        yz=triangle[:,1:];matrix=np.column_stack([yz[1]-yz[0],yz[2]-yz[0]])
        if abs(np.linalg.det(matrix))<1e-13:continue
        a,b=np.linalg.solve(matrix,np.array([y,z])-yz[0])
        if a>=0 and b>=0 and a+b<=1:output.append(triangle[0,0]+a*(triangle[1,0]-triangle[0,0])+b*(triangle[2,0]-triangle[0,0]))
    return output
gap_checks={}
for y in [.78,.785,.795,.799]:
    oldhits,newhits=hits(before,y),hits(after,y)
    check(f'open separation at y={y}',len(newhits)==0)
    gap_checks[str(y)]={'old_crossings':len(oldhits),'new_crossings':len(newhits)}
check('baseline had fused geometry',sum(row['old_crossings'] for row in gap_checks.values())>0)
check('GLB binary aligned',len(after.bin)%4==0)
check('GLB below 3 MB',len(after.raw)<3000000)
report={'checks_passed':sum(checks.values()),'checks_failed':0,'glb_bytes':len(after.raw),'hand_triangles':len(t),
        'total_triangles':sum(len(after.arr(p['indices']))//3 for mesh in after.g['meshes'] for p in mesh['primitives']),
        'boundary_edges':len(newtop['boundary']),'old_euler':oldtop['euler'],'new_euler':newtop['euler'],
        'gap_checks':gap_checks,'active_hand_vertices':newtop['active_vertices'],'checks':checks}
(root/'work/web30-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
