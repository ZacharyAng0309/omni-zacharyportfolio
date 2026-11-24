"""Bake existing albedo onto a clean eye-surface topology with seam-unwrapped UVs."""
import bpy,numpy as np,sys,json
from pathlib import Path
from collections import defaultdict
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
asset=Asset(root/'outputs/zachary_character_v33_candidate.glb');p=asset.prim('SM_Character_Face');source_points=asset.pos('SM_Character_Face');source_uv=asset.arr(p['attributes']['TEXCOORD_0']);source_tri=asset.arr(p['indices']).reshape(-1,3)
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(root/'outputs/zachary_character_v33_candidate.glb'))
source=bpy.data.objects['SM_Character_Face']
raw=np.load(root/'work/eye34-retopo.npz');points=raw['points'];tri=raw['triangles'];source_ids=raw['source_ids'];patched=raw['patched']
conversion=np.array([[1,0,0],[0,0,-1],[0,1,0]]);coords=points@conversion.T
mesh=bpy.data.meshes.new('GEO_FaceEyeSurface_v34');mesh.from_pydata(coords.tolist(),[],tri.tolist());mesh.update()
target=bpy.data.objects.new('BAKE_FaceEyeSurface_v34',mesh);bpy.context.scene.collection.objects.link(target)
keys={tuple(np.rint(v.astype(float)*1e6).astype('i8')):i for i,v in enumerate(points)}
source_to_geo=np.array([keys[tuple(np.rint(v.astype(float)*1e6).astype('i8'))] for v in source_points])
edge_uv=defaultdict(set)
for indices in source_tri:
 for aa,bb in [(indices[0],indices[1]),(indices[1],indices[2]),(indices[2],indices[0])]:
  ga,gb=source_to_geo[aa],source_to_geo[bb]
  if ga>gb:ga,gb,aa,bb=gb,ga,bb,aa
  edge_uv[(int(ga),int(gb))].add(tuple(np.rint(np.r_[source_uv[aa],source_uv[bb]]*1e6).astype('i8')))
for edge in mesh.edges:edge.use_seam=len(edge_uv.get(tuple(sorted(edge.vertices)),set()))>1
for obj in bpy.context.selected_objects:obj.select_set(False)
target.select_set(True);bpy.context.view_layer.objects.active=target
mesh.uv_layers.new(name='UV_Face_v34')
for vertex in mesh.vertices:vertex.select=True
for edge in mesh.edges:edge.select=True
for polygon in mesh.polygons:polygon.select=True;polygon.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
image=bpy.data.images.new('T_Face_v34_Albedo',width=2048,height=2048,alpha=False);image.generated_color=(.5,.3,.2,1)
material=bpy.data.materials.new('M_Face_v34_Bake');material.use_nodes=True
node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;material.node_tree.nodes.active=node;mesh.materials.append(material)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.002;scene.render.bake.max_ray_distance=.015
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=16
for obj in scene.objects:
 if obj.type=='MESH':obj.hide_render=obj not in [source,target]
source.select_set(True);target.select_set(True);bpy.context.view_layer.objects.active=target
bpy.ops.object.bake(type='DIFFUSE')
image.filepath_raw=str(root/'work/eye34-albedo.png');image.file_format='PNG';image.save()
bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');material.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.65
source.hide_render=True
np.savez(root/'work/eye34-baked-data.npz',points=points,triangles=tri,source_ids=source_ids,patched=patched,uv=np.array([[mesh.uv_layers.active.data[i].uv[:] for i in poly.loop_indices] for poly in mesh.polygons]),normals=np.array([v.normal[:] for v in mesh.vertices])@conversion)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/eye34-bake.blend'),compress=True)
print(json.dumps({'triangles':len(tri),'bake_resolution':2048,'seam_edges':sum(e.use_seam for e in mesh.edges)}))
