import bpy,json
from pathlib import Path
scene=bpy.context.scene; hair=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith('SM_Character_Hair'))
tree=hair.data.materials[0].node_tree
for o in scene.objects: o.select_set(False)
hair.select_set(True); bpy.context.view_layer.objects.active=hair
scene.cycles.samples=8; scene.render.bake.use_selected_to_active=False; scene.render.bake.margin=12
result=[]
for label,kind in [('albedo','DIFFUSE'),('normal','NORMAL')]:
 image=bpy.data.images.new('T_Hair_v22_'+label,width=2048,height=2048,alpha=False)
 image.colorspace_settings.name='Non-Color' if label=='normal' else 'sRGB'
 node=tree.nodes.new('ShaderNodeTexImage'); node.image=image
 for n in tree.nodes: n.select=False
 node.select=True; tree.nodes.active=node
 scene.render.bake.use_pass_direct=False; scene.render.bake.use_pass_indirect=False; scene.render.bake.use_pass_color=True
 scene.render.bake.normal_space='TANGENT'
 bpy.ops.object.bake(type=kind)
 image.filepath_raw=rf'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\hair-v22-{label}.png'; image.file_format='PNG'; image.save()
 result.append({'map':label,'bytes':Path(image.filepath_raw).stat().st_size})
scene.cycles.samples=32
print(json.dumps(result))
