"""Introduce a lip aperture and recessed oral cavity, with compatible named morphs.

Existing face vertex indices are retained. The Boolean supplies the local slit
and cavity; new outer vertices inherit UVs/weights/expressions barycentrically.
The oral cavity is a separate semantic mesh with synchronized target names.
"""
import bpy,bmesh,sys,json,copy,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
asset=Asset(root/'outputs/zachary_character_v31_candidate.glb')
mesh_index=next(i for i,m in enumerate(asset.g['meshes']) if m['name']=='SM_Character_Face')
source_mesh=asset.g['meshes'][mesh_index];primitive=source_mesh['primitives'][0];attributes=primitive['attributes']
arrays={name:asset.arr(index).copy() for name,index in attributes.items()}
points=arrays['POSITION'];triangles=asset.arr(primitive['indices']).reshape(-1,3).copy()
old_targets=[asset.arr(target['POSITION']).copy() for target in primitive['targets']]
scene=bpy.context.scene
for obj in list(scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
def key(point):return tuple(np.rint(np.asarray(point,dtype=float)*1e7).astype(np.int64))
_,first,welded=np.unique(np.rint(points.astype(float)*1e6).astype(np.int64),axis=0,return_index=True,return_inverse=True)
mesh=bpy.data.meshes.new('GEO_FaceMouthRepair');mesh.from_pydata(points[first].tolist(),[],welded[triangles].tolist());mesh.update()
uv_layer=mesh.uv_layers.new(name='UVMap')
for polygon,source_triangle in zip(mesh.polygons,triangles):
    for loop_index,source_index in zip(polygon.loop_indices,source_triangle):uv_layer.data[loop_index].uv=arrays['TEXCOORD_0'][source_index]
obj=bpy.data.objects.new('SM_FaceMouthRepair',mesh);scene.collection.objects.link(obj)
skin_material=bpy.data.materials.new('M_ExistingSkin');oral_material=bpy.data.materials.new('M_OralInterior')
mesh.materials.append(skin_material);mesh.materials.append(oral_material)
half_width=.025;half_gap=.00020
def line(x):return 1.5215-.0015*(np.asarray(x)/half_width)**2
profile=[(half_width*math.cos(t),float(line(half_width*math.cos(t)))+half_gap*math.sin(t)) for t in np.linspace(0,2*math.pi,65)[:-1]]
count=len(profile);cutter_points=[(x,y,z) for z in [.060,.145] for x,y in profile]
cutter_faces=[(i,(i+1)%count,count+(i+1)%count,count+i) for i in range(count)]
cutter_faces += [tuple(reversed(range(count))),tuple(range(count,2*count))]
cutter_mesh=bpy.data.meshes.new('GEO_LipApertureCutter');cutter_mesh.from_pydata(cutter_points,[],cutter_faces)
cutter_mesh.materials.append(skin_material);cutter_mesh.materials.append(oral_material)
for polygon in cutter_mesh.polygons:polygon.material_index=1
bm=bmesh.new();bm.from_mesh(cutter_mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cutter_mesh);bm.free()
cutter=bpy.data.objects.new('BOOL_LipOpening',cutter_mesh);scene.collection.objects.link(cutter)
modifier=obj.modifiers.new('Lip opening and recessed cavity','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
if hasattr(modifier,'use_self'):modifier.use_self=False
if hasattr(modifier,'use_hole_tolerant'):modifier.use_hole_tolerant=True
bpy.context.view_layer.update()
evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());result=evaluated.to_mesh()
bm=bmesh.new();bm.from_mesh(result)
bmesh.ops.dissolve_degenerate(bm,dist=.00002,edges=[e for e in bm.edges if all(abs(v.co.x)<.027 and 1.518<v.co.y<1.524 for v in e.verts)])
bmesh.ops.triangulate(bm,faces=list(bm.faces))
flaps=[f for f in bm.faces if f.calc_area()<1e-8 and sorted(len(e.link_faces) for e in f.edges)==[1,3,3]]
bmesh.ops.delete(bm,geom=flaps,context='FACES_ONLY')
mouth_boundary=[e for e in bm.edges if len(e.link_faces)==1 and all(abs(v.co.x)<.027 and 1.518<v.co.y<1.524 for v in e.verts)]
if mouth_boundary:
    filled=bmesh.ops.holes_fill(bm,edges=mouth_boundary,sides=3)['faces']
    for face in filled:
        adjacent=[other.material_index for edge in face.edges for other in edge.link_faces if other!=face]
        face.material_index=max(set(adjacent),key=adjacent.count) if adjacent else 0
    bmesh.ops.recalc_face_normals(bm,faces=filled)
bm.normal_update();bm.to_mesh(result);bm.free();result.update();result.calc_loop_triangles()
result_points=np.array([v.co[:] for v in result.vertices]);result_normals=np.array([v.normal[:] for v in result.vertices])
result_triangles=np.array([t.vertices[:] for t in result.loop_triangles],dtype=int)
result_materials=np.array([result.polygons[t.polygon_index].material_index for t in result.loop_triangles])
result_uvs=np.array([[result.uv_layers.active.data[i].uv[:] for i in t.loops] for t in result.loop_triangles])
assert sum(result_materials==1)>20,'The cutter must provide a separate oral surface'
np.savez(root/'work/mouth32-boolean-raw.npz',points=result_points,triangles=result_triangles,materials=result_materials)
face_lookup={tuple(sorted(key(points[i]) for i in tri)):tri for tri in triangles}
source_bvh=BVHTree.FromPolygons([Vector(p) for p in points],triangles.tolist(),all_triangles=True)
by_position={}
for i,point in enumerate(points):by_position.setdefault(key(point),[]).append(i)
new_arrays={name:[row.copy() for row in rows] for name,rows in arrays.items()}
new_targets=[[row.copy() for row in rows] for rows in old_targets]
new_lookup={};canonical_weights={};outer=[];oral=[];unchanged=0
def barycentric(point,triangle):
    a,b,c=np.asarray(triangle,dtype=np.float64);v0=b-a;v1=c-a;v2=point-a
    d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1
    denominator=d00*d11-d01*d01
    if denominator<=1e-24:
        values=np.zeros(3);values[np.argmin(np.linalg.norm(triangle-point,axis=1))]=1
        return values
    v=(d11*d20-d01*d21)/denominator;w=(d00*d21-d01*d20)/denominator
    values=np.maximum([1-v-w,v,w],0);return values/values.sum()
for tri,material,triangle_uvs in zip(result_triangles,result_materials,result_uvs):
    vertices=result_points[tri];signature=tuple(sorted(key(point) for point in vertices))
    destination=oral if material==1 else outer
    if material==0 and signature in face_lookup:
        destination.append(face_lookup[signature]);unchanged+=1;continue
    center=vertices.mean(axis=0);near,normal,face_index,distance=source_bvh.find_nearest(Vector(center));source_indices=triangles[face_index]
    face=[]
    for result_index,point,result_uv in zip(tri,vertices,triangle_uvs):
        matches=by_position.get(key(point),[])
        if material==0 and matches:
            match=min(matches,key=lambda i:np.linalg.norm(arrays['TEXCOORD_0'][i]-result_uv))
            if np.linalg.norm(arrays['TEXCOORD_0'][match]-result_uv)<1e-5:face.append(match);continue
        nearest,_,nearest_index,_=source_bvh.find_nearest(Vector(point));transfer_indices=triangles[nearest_index]
        transfer_b=barycentric(np.array(nearest),points[transfer_indices])
        uv=result_uv if material==0 else transfer_b@arrays['TEXCOORD_0'][transfer_indices]
        signature=(material,key(point),tuple(np.rint(uv*1e6).astype(np.int64)))
        if signature in new_lookup:face.append(new_lookup[signature]);continue
        index=len(new_arrays['POSITION']);new_lookup[signature]=index;face.append(index)
        new_arrays['POSITION'].append(point)
        normal=transfer_b@arrays['NORMAL'][transfer_indices] if material==0 else result_normals[result_index].copy()
        normal/=max(np.linalg.norm(normal),1e-12)
        new_arrays['NORMAL'].append(normal);new_arrays['TEXCOORD_0'].append(uv)
        position_key=key(point)
        if position_key not in canonical_weights:
            dense={}
            for vertex,amount in zip(transfer_indices,transfer_b):
                for joint,weight in zip(arrays['JOINTS_0'][vertex],arrays['WEIGHTS_0'][vertex]):
                    dense[int(joint)]=dense.get(int(joint),0)+amount*weight
            selected=sorted(dense,key=dense.get,reverse=True)[:4]
            while len(selected)<4:selected.append(0)
            values=np.array([dense.get(j,0) for j in selected]);values/=values.sum()
            canonical_weights[position_key]=(selected,values)
        selected,values=canonical_weights[position_key]
        new_arrays['JOINTS_0'].append(selected);new_arrays['WEIGHTS_0'].append(values)
        for target_index,target in enumerate(old_targets):new_targets[target_index].append(transfer_b@target[transfer_indices])
    destination.append(face)
evaluated.to_mesh_clear()
new_positions=np.array(new_arrays['POSITION'],dtype=float)
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
x,y,z=new_positions.T;centerline=line(x);signed=y-centerline
horizontal=np.clip(1-(x/half_width)**2,0,1)
upper=signed>=0
front=smooth(.035,.080,z)
oral_vertices=set(np.asarray(oral).ravel())
oral_mask=np.array([i in oral_vertices for i in range(len(new_positions))])
front[oral_mask]=1
local=(1-smooth(.006,.023,abs(signed)))*horizontal*front
branch=np.clip(signed/np.maximum(half_gap*np.sqrt(horizontal),.00002),-1,1)
opening=np.zeros_like(new_positions)
opening[:,1]=np.where(upper,.0020,.0060)*branch*local
opening[:,2]=-.0010*local
new_targets[2]=opening
# Art-directed jaw rotation, softly blended into cheeks and neck.
hinge=np.array([0.,1.550,.012]);angle=.13
rotation=np.array([[1,0,0],[0,math.cos(angle),-math.sin(angle)],[0,math.sin(angle),math.cos(angle)]])
rotated=(new_positions-hinge)@rotation.T+hinge
jaw_weight=(1-smooth(.035,.065,abs(x)))*smooth(1.435,1.485,y)*(1-smooth(.003,.018,signed))*front
jaw_weight*=np.clip(-branch,0,1)
lip_transition=1-smooth(.002,.012,abs(signed))
jaw_weight*=1-lip_transition*(1-np.sqrt(horizontal))
jaw=(rotated-new_positions)*jaw_weight[:,None]
new_targets[3]=jaw
new_targets[7]=opening*.85+jaw*.55

def append_accessor(values,kind,component=5126,target=34962):
    values=np.asarray(values,dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[component])
    asset.bin.extend(b'\x00'*((-len(asset.bin))%4));offset=len(asset.bin);payload=values.tobytes();asset.bin.extend(payload)
    view={'buffer':0,'byteOffset':offset,'byteLength':len(payload)}
    if target:view['target']=target
    view_index=len(asset.g['bufferViews']);asset.g['bufferViews'].append(view)
    acc={'bufferView':view_index,'componentType':component,'count':len(values),'type':kind}
    if kind=='VEC3':acc.update(min=values.min(axis=0).tolist(),max=values.max(axis=0).tolist())
    index=len(asset.g['accessors']);asset.g['accessors'].append(acc);return index
def replace_accessor(index,values):
    old=asset.g['accessors'][index];new_index=append_accessor(values,old['type'],old['componentType'],34963 if index==primitive['indices'] else 34962)
    new=asset.g['accessors'].pop();asset.g['accessors'][index]=new
for name,index in attributes.items():replace_accessor(index,new_arrays[name])
for i,target in enumerate(primitive['targets']):replace_accessor(target['POSITION'],new_targets[i])
replace_accessor(primitive['indices'],np.asarray(outer).reshape(-1,1))
oral_material_index=len(asset.g['materials']);asset.g['materials'].append({'name':'Zachary_Oral_Cavity',
 'pbrMetallicRoughness':{'baseColorFactor':[.045,.008,.012,1],'metallicFactor':0,'roughnessFactor':.86},'doubleSided':True,
 'extensions':{'KHR_materials_specular':{'specularFactor':.12}}})
oral_primitive={'attributes':copy.deepcopy(attributes),'indices':append_accessor(np.asarray(oral).reshape(-1,1),'SCALAR',5123,34963),
 'material':oral_material_index,'mode':4,'targets':copy.deepcopy(primitive['targets'])}
oral_mesh_index=len(asset.g['meshes']);asset.g['meshes'].append({'name':'SM_Character_OralCavity','primitives':[oral_primitive],
 'extras':copy.deepcopy(source_mesh['extras']),'weights':[0]*8})
source_node_index=next(i for i,n in enumerate(asset.g['nodes']) if n.get('mesh')==mesh_index)
oral_node=copy.deepcopy(asset.g['nodes'][source_node_index]);oral_node.update(name='SM_Character_OralCavity',mesh=oral_mesh_index);oral_node.pop('children',None)
oral_node_index=len(asset.g['nodes']);asset.g['nodes'].append(oral_node)
parents=[node for node in asset.g['nodes'][:-1] if source_node_index in node.get('children',[])]
if parents:
    for parent in parents:parent['children'].append(oral_node_index)
else:
    for s in asset.g['scenes']:
        if source_node_index in s['nodes']:s['nodes'].append(oral_node_index)
asset.bin.extend(b'\x00'*((-len(asset.bin))%4));asset.g['buffers'][0]['byteLength']=len(asset.bin)
asset.save(root/'outputs/zachary_character_v32_candidate.glb')
report={'method':'rounded lip slit and recessed Boolean oral cavity; transferred surface attributes and revised mouth/jaw/aa targets',
 'original_face_vertices':len(points),'total_face_vertices':len(new_positions),'original_triangles':len(triangles),
 'outer_triangles':len(outer),'oral_triangles':len(oral),'unchanged_outer_triangles':unchanged,
 'neutral_aperture_mm':half_gap*2000,'depth_back_m':.060,
 'integration_requirement':'Drive matching morph target names on both SM_Character_Face and SM_Character_OralCavity.'}
(root/'work/mouth32-changes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

