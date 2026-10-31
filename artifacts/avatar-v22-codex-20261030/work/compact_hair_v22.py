import bpy
from pathlib import Path
scene=bpy.context.scene; hair=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith('SM_Character_Hair')); tree=hair.data.materials[0].node_tree
image=bpy.data.images['T_Hair_v22_albedo']; image.file_format='WEBP'; image.filepath_raw=r'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\hair-v22-albedo.webp'; image.save()
normal=bpy.data.images.new('T_Hair_v22_normal_compact',width=1024,height=1024,alpha=False); normal.colorspace_settings.name='Non-Color'
node=tree.nodes.new('ShaderNodeTexImage'); node.image=normal
for n in tree.nodes:n.select=False
node.select=True; tree.nodes.active=node
scene.cycles.samples=8
bpy.ops.object.bake(type='NORMAL')
normal.file_format='PNG'; normal.filepath_raw=r'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\hair-v22-normal.png'; normal.save()
scene.cycles.samples=32
print('albedo bytes',Path(image.filepath_raw).stat().st_size,'normal bytes',Path(normal.filepath_raw).stat().st_size)
