"""Bake the strand material to the existing hair atlas without changing UVs."""
import bpy,numpy as np,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];scene=bpy.data.scenes['Portrait review v37'];bpy.context.window.scene=scene
hair=next(o for o in scene.objects if o.name.startswith('SM_Character_Hair'));tree=hair.data.materials[0].node_tree
hair.data.uv_layers.active_index=1;hair.data.uv_layers[1].active_render=True
for o in scene.objects:o.select_set(False)
hair.select_set(True);bpy.context.view_layer.objects.active=hair
scene.cycles.samples=16;scene.render.bake.use_selected_to_active=False;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.normal_space='TANGENT';scene.render.bake.use_clear=True
report={}
for label,kind,resolution in [('albedo','DIFFUSE',2048),('normal','NORMAL',1024),('parameters','EMIT',512)]:
 if kind=='EMIT':
  rough=next(n for n in tree.nodes if n.label=='V38_ROUGHNESS').outputs[0];spec=next(n for n in tree.nodes if n.label=='V38_SPECULAR_HALF').outputs[0]
  channels=tree.nodes.new('ShaderNodeCombineColor');tree.links.new(rough,channels.inputs['Green']);twice=tree.nodes.new('ShaderNodeMath');twice.operation='MULTIPLY';twice.inputs[1].default_value=2;tree.links.new(spec,twice.inputs[0]);tree.links.new(twice.outputs[0],channels.inputs['Red']);channels.inputs['Blue'].default_value=0
  emission=tree.nodes.new('ShaderNodeEmission');tree.links.new(channels.outputs[0],emission.inputs['Color']);output=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL');tree.links.new(emission.outputs[0],output.inputs['Surface'])
 image=bpy.data.images.new('T_Hair_v38_'+label,width=resolution,height=resolution,alpha=kind=='EMIT')
 image.colorspace_settings.name='sRGB' if label=='albedo' else 'Non-Color'
 if kind=='EMIT':image.alpha_mode='CHANNEL_PACKED'
 target=tree.nodes.new('ShaderNodeTexImage');target.image=image
 for n in tree.nodes:n.select=False
 target.select=True;tree.nodes.active=target;scene.render.bake.margin=12 if resolution==2048 else 6 if resolution==1024 else 3
 bpy.ops.object.bake(type=kind)
 if kind=='EMIT':
  values=np.array(image.pixels[:],dtype='f4').reshape(-1,4);values[:,3]=values[:,0];values[:,0]=1;image.pixels.foreach_set(values.ravel());image.update()
 image.file_format='PNG';path=root/f'work/hair38-{label}-raw.png';image.save(filepath=str(path));report[label]={'resolution':resolution,'raw_bytes':path.stat().st_size}
(root/'work/hair38-bake.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
