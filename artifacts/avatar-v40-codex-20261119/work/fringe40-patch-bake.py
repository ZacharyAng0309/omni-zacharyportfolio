"""Unwrap the local repair patch into proven unused space in each existing atlas."""
import bpy,bmesh,sys,json,hashlib,numpy as np
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'work/fringe40-shape.glb');scene=bpy.data.scenes['Portrait review v39'];bpy.context.window.scene=scene
names=['SM_Character_Face','SM_Character_Hair'];vertices=[];triangles=[];uv0=[];uv1=[];source_tri=[];source_mesh=[];materials=[];images=[]
for mi,name in enumerate(names):
 obj=next(o for o in scene.objects if o.name==name);material=obj.data.materials[0].copy();materials.append(material);shader=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');images.append(shader.inputs['Base Color'].links[0].from_node.inputs[1].links[0].from_node.image)
 p=a.prim(name);x=a.pos(name);t=a.arr(p['indices']).reshape(-1,3);u0=a.arr(p['attributes']['TEXCOORD_0']);u1=a.arr(p['attributes']['TEXCOORD_1'])
 for ti,ids in enumerate(t):
  pts=x[ids];lo=pts.min(0);hi=pts.max(0)
  if hi[0]<-.086 or lo[0]>.086 or hi[1]<1.618 or lo[1]>1.715 or hi[2]<.050:continue
  base=len(vertices);vertices.extend([[float(v[0]),float(-v[2]),float(v[1])] for v in pts]);triangles.append([base,base+1,base+2]);uv0.extend([(float(v[0]),float(1-v[1])) for v in u0[ids]]);uv1.extend([(float(v[0]),float(1-v[1])) for v in u1[ids]]);source_tri.append(ti);source_mesh.append(mi)
mesh=bpy.data.meshes.new('Fringe40RepairPatch');mesh.from_pydata(vertices,[],triangles);mesh.update()
for name,values in [('UVMap',uv0),('UVMap.001',uv1)]:
 layer=mesh.uv_layers.new(name=name)
 for loop,co in zip(layer.data,values):loop.uv=co
mesh.attributes.new('source_triangle','INT','FACE').data.foreach_set('value',np.asarray(source_tri,dtype='i4'))
mesh.attributes.new('source_mesh','INT','FACE').data.foreach_set('value',np.asarray(source_mesh,dtype='i4'))
for mat in materials:mesh.materials.append(mat)
for poly,mi in zip(mesh.polygons,source_mesh):poly.material_index=mi
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
for edge in bm.edges:
 if len({f.material_index for f in edge.link_faces})>1:edge.seam=True
bm.to_mesh(mesh);bm.free();mesh.update()
obj=bpy.data.objects.new('BAKE_Fringe40RepairPatch',mesh);scene.collection.objects.link(obj)
for item in scene.objects:item.select_set(False)
obj.select_set(True);bpy.context.view_layer.objects.active=obj;uv=mesh.uv_layers.new(name='UV_FringeRepair40');mesh.uv_layers.active=uv;uv.active_render=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.015);bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(margin=.02,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
mesh=obj.data;uv=mesh.uv_layers['UV_FringeRepair40'];mesh.uv_layers.active_index=len(mesh.uv_layers)-1;uv.active_render=True
local=np.array([v.uv[:] for v in uv.data]);local=(local-local.min(0))/np.maximum(np.ptp(local,axis=0),1e-8)
metadata=[]
for poly in mesh.polygons:
 mi=mesh.attributes['source_mesh'].data[poly.index].value;ti=mesh.attributes['source_triangle'].data[poly.index].value;q=a.prim(names[mi]);ids=a.arr(q['indices']).reshape(-1,3)[ti];expected=a.pos(names[mi])[ids];pairs=[]
 for loop in poly.loop_indices:
  v=mesh.vertices[mesh.loops[loop].vertex_index].co;actual=np.array([v.x,v.z,-v.y]);distance=np.linalg.norm(expected-actual,axis=1);corner=int(distance.argmin());assert distance[corner]<2e-6;pairs.append((corner,loop))
 assert sorted(c for c,l in pairs)==[0,1,2];order=[l for c,l in sorted(pairs)]
 metadata.append({'mesh':mi,'triangle':ti,'loops':order})
scene.cycles.samples=16;scene.render.bake.use_selected_to_active=False;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=4
rects={'face':[896,16,768,768],'hair':[1264,400,768,768]};result={};report={}
for mi,label in enumerate(['face','hair']):
 original=images[mi];image=original.copy();image.name='T_Fringe40_Atlas_'+label;w,h=image.size;x,y,rw,rh=rects[label]
 mapped=np.column_stack(((x+8+local[:,0]*(rw-16))/w,1-(y+8+(1-local[:,1])*(rh-16))/h))
 uv=mesh.uv_layers['UV_FringeRepair40'];mesh.uv_layers.active_index=len(mesh.uv_layers)-1;uv.active_render=True
 for loop,value in zip(uv.data,mapped):loop.uv=value
 mesh.update();actual=np.array([v.uv[:] for v in mesh.uv_layers['UV_FringeRepair40'].data]);assert np.max(abs(actual-mapped))<1e-6
 print('ACTIVE_BAKE_UV',label,mesh.uv_layers.active.name,[(l.name,l.active_render) for l in mesh.uv_layers],actual.min(0).tolist(),actual.max(0).tolist(),flush=True)
 for mat in materials:
  tree=mat.node_tree;target=tree.nodes.new('ShaderNodeTexImage');target.image=image;tree.nodes.active=target
  for n in tree.nodes:n.select=False
  target.select=True
 scene.render.bake.use_clear=False;bpy.ops.object.bake(type='DIFFUSE');image.file_format='PNG';image.save(filepath=str(root/f'work/fringe40-{label}-raw.png'))
 result[label]=np.array([mapped[row['loops']]*[1,-1]+[0,1] for row in metadata])
 report[label]={'rectangle_pixels':rects[label],'resolution':[w,h],'patch_triangles':len(metadata),'source_triangles_using_patch':sum(row['mesh']==mi for row in metadata)}
np.savez(root/'work/fringe40-patch-uv.npz',face=result['face'],hair=result['hair'],source_mesh=np.array([r['mesh'] for r in metadata],dtype='i4'),source_triangle=np.array([r['triangle'] for r in metadata],dtype='i4'),local_uv=np.array([local[r['loops']] for r in metadata]))
report['verified_files']={name:hashlib.sha256((root/'work'/name).read_bytes()).hexdigest() for name in ['fringe40-face-raw.png','fringe40-hair-raw.png','fringe40-patch-uv.npz']}
(root/'work/fringe40-patch-bake.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
