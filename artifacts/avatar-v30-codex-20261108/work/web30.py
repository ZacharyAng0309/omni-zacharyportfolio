"""Open the fused middle/ring finger webs with a rounded, localized cutter.

Original hand vertices retain their indices and attributes. New cut-surface
vertices receive barycentrically transferred UVs and skin weights. Other
meshes, rig transforms, facial morphs and embedded images remain untouched.
"""
import bpy,sys,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
asset=Asset(root/'outputs/zachary_character_v29_candidate.glb')
primitive=asset.prim('SM_Character_Hands');attributes=primitive['attributes']
arrays={name:asset.arr(index).copy() for name,index in attributes.items()}
points=arrays['POSITION'];triangles=asset.arr(primitive['indices']).reshape(-1,3).copy()
scene=bpy.context.scene
for obj in list(scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
_,first,welded=np.unique(np.rint(points.astype(float)*1e6).astype(np.int64),axis=0,return_index=True,return_inverse=True)
mesh=bpy.data.meshes.new('GEO_HandRepair');mesh.from_pydata(points[first].tolist(),[],welded[triangles].tolist());mesh.update()
obj=bpy.data.objects.new('SM_HandRepair',mesh);scene.collection.objects.link(obj)
# Rounded slot follows the observed gap between middle and ring fingers.
radius=.0022;top=.8008;bottom=.730
profile=[]
for angle in np.linspace(0,math.pi,17):
    y=top+radius*math.sin(angle);offset=radius*math.cos(angle)
    profile.append((y,.064-.16*(y-.775)+offset))
for angle in np.linspace(math.pi,2*math.pi,17):
    y=bottom+radius*math.sin(angle);offset=radius*math.cos(angle)
    profile.append((y,.064-.16*(y-.775)+offset))
count=len(profile);cutter_points=[(x,y,z) for x in [-.50,.50] for y,z in profile]
cutter_faces=[]
for i in range(count):j=(i+1)%count;cutter_faces.append((i,j,count+j,count+i))
cutter_faces += [tuple(reversed(range(count))),tuple(range(count,2*count))]
cutter_mesh=bpy.data.meshes.new('GEO_RoundedWebCutter');cutter_mesh.from_pydata(cutter_points,[],cutter_faces);cutter_mesh.update()
# Ensure the cutter is consistently outward-facing through bmesh.
import bmesh
bm=bmesh.new();bm.from_mesh(cutter_mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cutter_mesh);bm.free()
cutter=bpy.data.objects.new('BOOL_FingerWeb',cutter_mesh);scene.collection.objects.link(cutter)
modifier=obj.modifiers.new('Open fused finger webs','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
if hasattr(modifier,'use_hole_tolerant'):modifier.use_hole_tolerant=True
if hasattr(modifier,'use_self'):modifier.use_self=True
bpy.context.view_layer.update()
evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());result=evaluated.to_mesh()
cleanup=bmesh.new();cleanup.from_mesh(result)
short_edges=[edge for edge in cleanup.edges if edge.calc_length()<.00008]
if short_edges:bmesh.ops.dissolve_degenerate(cleanup,dist=.00008,edges=short_edges)
bmesh.ops.recalc_face_normals(cleanup,faces=list(cleanup.faces));cleanup.to_mesh(result);cleanup.free()
result.calc_loop_triangles()
result_points=np.array([v.co[:] for v in result.vertices]);result_normals=np.array([v.normal[:] for v in result.vertices])
result_triangles=np.array([t.vertices[:] for t in result.loop_triangles],dtype=int)
# Remove tiny triangulation flaps, identified by two over-subscribed edges
# and one exposed edge. These are generated cut faces, not source anatomy.
_,ri=np.unique(np.rint(result_points*1e6).astype(np.int64),axis=0,return_inverse=True)
rf=ri[result_triangles]
re=np.sort(np.concatenate([rf[:,[0,1]],rf[:,[1,2]],rf[:,[2,0]]]),axis=1)
unique_edges,multiplicity=np.unique(re,axis=0,return_counts=True)
edge_counts={tuple(edge):int(number) for edge,number in zip(unique_edges,multiplicity)}
keep=[];removed_flaps=0
source_keys=set(map(tuple,np.rint(points.astype(float)*1e6).astype(np.int64)))
for indices,face in zip(result_triangles,rf):
    counts=sorted(edge_counts[tuple(sorted((face[a],face[b])))] for a,b in [(0,1),(1,2),(2,0)])
    q=result_points[indices];area=np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))/2
    if counts==[1,3,3] and area<1e-7:
        assert any(tuple(np.rint(point*1e6).astype(np.int64)) not in source_keys for point in q)
        removed_flaps+=1
    else:keep.append(indices)
result_triangles=np.array(keep,dtype=int)
np.savez(root/'work/web30-boolean-raw.npz',points=result_points,triangles=result_triangles,normals=result_normals)
assert len(result_triangles)>len(triangles)-300,(len(triangles),len(result_triangles))
def key(point):return tuple(np.rint(np.asarray(point,dtype=float)*1e6).astype(np.int64))
face_lookup={tuple(sorted(key(points[i]) for i in tri)):tri for tri in triangles}
source_bvh=BVHTree.FromPolygons([Vector(p) for p in points],triangles.tolist(),all_triangles=True)
by_position={}
for i,point in enumerate(points):by_position.setdefault(key(point),[]).append(i)
new_arrays={name:[row.copy() for row in rows] for name,rows in arrays.items()}
new_lookup={};weight_lookup={};output_triangles=[];unchanged=0;added=[]
def barycentric(point,triangle):
    a,b,c=triangle;v0=b-a;v1=c-a;v2=point-a
    d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1
    denominator=d00*d11-d01*d01
    v=(d11*d20-d01*d21)/denominator;w=(d00*d21-d01*d20)/denominator
    values=np.maximum([1-v-w,v,w],0);return values/values.sum()
for tri in result_triangles:
    vertices=result_points[tri]
    signature=tuple(sorted(key(point) for point in vertices))
    if signature in face_lookup:
        output_triangles.append(face_lookup[signature]);unchanged+=1;continue
    center=vertices.mean(axis=0)
    location,normal,face_index,distance=source_bvh.find_nearest(Vector(center))
    assert face_index is not None
    source_indices=triangles[face_index]
    face=[]
    for result_index,point in zip(tri,vertices):
        matches=by_position.get(key(point),[])
        source_matches=[i for i in matches if i in source_indices]
        if source_matches:
            face.append(source_matches[0]);continue
        if matches:
            face.append(matches[0]);continue
        b=barycentric(point,points[source_indices])
        uv=b@arrays['TEXCOORD_0'][source_indices]
        signature=(key(point),tuple(np.rint(uv*1e6).astype(np.int64)))
        if signature in new_lookup:face.append(new_lookup[signature]);continue
        index=len(new_arrays['POSITION']);new_lookup[signature]=index;face.append(index)
        new_arrays['POSITION'].append(point)
        n=result_normals[result_index];n/=max(np.linalg.norm(n),1e-12)
        new_arrays['NORMAL'].append(n)
        new_arrays['TEXCOORD_0'].append(uv)
        position_key=key(point)
        if position_key not in weight_lookup:
            nearest,_,nearest_index,_=source_bvh.find_nearest(Vector(point))
            weight_indices=triangles[nearest_index];weight_b=barycentric(np.array(nearest),points[weight_indices])
            dense={}
            for vertex,amount in zip(weight_indices,weight_b):
                for joint,weight in zip(arrays['JOINTS_0'][vertex],arrays['WEIGHTS_0'][vertex]):
                    dense[int(joint)]=dense.get(int(joint),0)+amount*weight
            selected=sorted(dense,key=dense.get,reverse=True)[:4]
            while len(selected)<4:selected.append(0)
            values=np.array([dense.get(j,0) for j in selected]);values/=values.sum()
            weight_lookup[position_key]=(selected,values)
        selected,values=weight_lookup[position_key]
        new_arrays['JOINTS_0'].append(selected);new_arrays['WEIGHTS_0'].append(values)
        added.append({'index':index,'source_triangle':int(face_index),'source_distance_mm':float(distance*1000)})
    output_triangles.append(face)
evaluated.to_mesh_clear()
def replace_accessor(index,values):
    accessor=asset.g['accessors'][index];dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[accessor['componentType']]
    values=np.asarray(values,dtype=dtype);asset.bin.extend(b'\x00'*((-len(asset.bin))%4))
    offset=len(asset.bin);payload=values.tobytes();asset.bin.extend(payload)
    view={'buffer':0,'byteOffset':offset,'byteLength':len(payload)}
    oldview=asset.g['bufferViews'][accessor['bufferView']]
    if 'target' in oldview:view['target']=oldview['target']
    accessor['bufferView']=len(asset.g['bufferViews']);accessor['byteOffset']=0;accessor['count']=len(values)
    asset.g['bufferViews'].append(view)
    if 'min' in accessor:accessor['min']=values.min(axis=0).tolist()
    if 'max' in accessor:accessor['max']=values.max(axis=0).tolist()
for name,index in attributes.items():replace_accessor(index,new_arrays[name])
replace_accessor(primitive['indices'],np.asarray(output_triangles).reshape(-1,1))
asset.bin.extend(b'\x00'*((-len(asset.bin))%4))
asset.g['buffers'][0]['byteLength']=len(asset.bin)
asset.save(root/'outputs/zachary_character_v30_candidate.glb')
report={'method':'Blender exact Boolean with rounded slot, original vertex indices retained; barycentric transfer on appended vertices',
        'slot_width_mm':radius*2000,'slot_top_y_m':top+radius,'original_vertices':len(points),'appended_vertices':len(added),
        'original_triangles':len(triangles),'result_triangles':len(output_triangles),'unchanged_triangles':unchanged,'removed_boolean_slivers':removed_flaps,
        'new_surface_transfer':added}
(root/'work/web30-changes.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='new_surface_transfer'}))
