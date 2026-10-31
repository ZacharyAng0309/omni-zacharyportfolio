import bpy
from mathutils import Vector
scene=bpy.context.scene
hair=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith('SM_Character_Hair'))
mat=hair.data.materials[0].copy(); mat.name='M_Hair_v22_StrandDetail'; hair.data.materials[0]=mat
tree=mat.node_tree; nodes=tree.nodes; links=tree.links
bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
original=bsdf.inputs['Base Color'].links[0].from_socket
tex=nodes.new('ShaderNodeTexCoord')
mapping=nodes.new('ShaderNodeVectorMath'); mapping.operation='MULTIPLY'; mapping.inputs[1].default_value=(1400,1400,70)
links.new(tex.outputs['Object'],mapping.inputs[0])
noise=nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=1; noise.inputs['Detail'].default_value=2; noise.inputs['Roughness'].default_value=0.6
links.new(mapping.outputs['Vector'],noise.inputs['Vector'])
ramp=nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=0.2; ramp.color_ramp.elements[0].color=(0.017,0.010,0.006,1); ramp.color_ramp.elements[1].position=0.8; ramp.color_ramp.elements[1].color=(0.038,0.024,0.014,1)
links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
mix=nodes.new('ShaderNodeMixRGB'); mix.blend_type='MIX'; mix.inputs[0].default_value=0.65
links.new(original,mix.inputs[1]); links.new(ramp.outputs['Color'],mix.inputs[2]); links.new(mix.outputs['Color'],bsdf.inputs['Base Color'])
bump=nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=0.32; bump.inputs['Distance'].default_value=0.00010
links.new(noise.outputs['Fac'],bump.inputs['Height']); links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
bsdf.inputs['Roughness'].default_value=0.52; bsdf.inputs['Specular IOR Level'].default_value=0.22
scene.camera.location=(0,-3,1.55); scene.camera.rotation_euler=(Vector((0,0,1.55))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=r'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\avatar-v22-hair-trial.png'
bpy.ops.render.render(write_still=True)
print('Hair shader trial ready.')
