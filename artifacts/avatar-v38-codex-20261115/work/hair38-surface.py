"""Part-guided strand material on the latest model, with native Cycles baking."""
import bpy, numpy as np, heapq, json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Portrait review v37'];bpy.context.window.scene=scene
hair=next(o for o in scene.objects if o.name.startswith('SM_Character_Hair'))
material=hair.data.materials[0];material.name='M_Hair_v38_CurtainFlow'
tree=material.node_tree;nodes=tree.nodes;links=tree.links
shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
oldcolor=shader.inputs['Base Color'].links[0].from_socket
oldrough=shader.inputs['Roughness'].links[0].from_socket
oldspec=shader.inputs['Specular IOR Level'].links[0].from_socket
oldnormal=shader.inputs['Normal'].links[0].from_socket
# Keep all existing image lookups on their original UV map during the bake.
for n in list(nodes):
 if n.type=='TEX_IMAGE' and not n.inputs['Vector'].is_linked:
  uv=nodes.new('ShaderNodeUVMap');uv.uv_map=hair.data.uv_layers[1].name;links.new(uv.outputs[0],n.inputs['Vector'])
points=np.array([v.co[:] for v in hair.data.vertices]);logical,inverse=np.unique(np.round(points,6),axis=0,return_inverse=True)
triangles=np.array([p.vertices[:] for p in hair.data.polygons]);lt=inverse[triangles]
edges,counts=np.unique(np.sort(np.concatenate([lt[:,[0,1]],lt[:,[1,2]],lt[:,[2,0]]]),axis=1),axis=0,return_counts=True)
neighbors=[[] for _ in logical]
for a,b in edges:
 length=float(np.linalg.norm(logical[a]-logical[b]));neighbors[a].append((b,length));neighbors[b].append((a,length))
boundary=np.unique(edges[counts==1]);distance=np.full(len(logical),np.inf);distance[boundary]=0;queue=[(0,int(i)) for i in boundary];heapq.heapify(queue)
while queue:
 d,i=heapq.heappop(queue)
 if d>distance[i]:continue
 for j,length in neighbors[i]:
  if d+length<distance[j]:distance[j]=d+length;heapq.heappush(queue,(d+length,int(j)))
weight=np.clip(distance[inverse]/.012,0,1);weight=weight*weight*(3-2*weight)
attribute=hair.data.attributes.new('hair38_boundary_falloff','FLOAT','POINT');attribute.data.foreach_set('value',weight.astype('f4'))
def math(op,a,b=0):
 n=nodes.new('ShaderNodeMath');n.operation=op
 for socket,val in zip(n.inputs[:2],(a,b)):
  if isinstance(val,(int,float)):socket.default_value=val
  else:links.new(val,socket)
 return n.outputs[0]
def ramp(value,lo,hi):
 n=nodes.new('ShaderNodeMapRange');n.interpolation_type='SMOOTHSTEP';links.new(value,n.inputs['Value']);n.inputs['From Min'].default_value=lo;n.inputs['From Max'].default_value=hi;return n.outputs[0]
def mix(a,b,w):
 n=nodes.new('ShaderNodeMixRGB');links.new(w,n.inputs[0])
 for socket,val in zip(n.inputs[1:3],(a,b)):
  if isinstance(val,tuple):socket.default_value=val
  else:links.new(val,socket)
 return n.outputs[0]
attr=nodes.new('ShaderNodeAttribute');attr.attribute_name=attribute.name
rgb=nodes.new('ShaderNodeSeparateColor');links.new(oldcolor,rgb.inputs[0])
# Existing warm/dark hair pixels plus seam falloff exclude skin and the cool cowl island.
dark=math('SUBTRACT',1,ramp(rgb.outputs['Red'],.045,.11))
warm=ramp(math('SUBTRACT',rgb.outputs['Red'],rgb.outputs['Blue']),.004,.013)
mask=math('MULTIPLY',attr.outputs['Fac'],math('MULTIPLY',dark,warm))
pos=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(pos.outputs['Position'],sep.inputs[0])
across=math('ADD',sep.outputs['X'],.014)
forward=math('SUBTRACT',.015,sep.outputs['Y']);up=math('SUBTRACT',sep.outputs['Z'],1.62)
# Tilt the flow pole toward the frontal part: the curtains fan out as they descend.
front_axis=math('SUBTRACT',math('MULTIPLY',forward,.94),math('MULTIPLY',up,.342))
angle=math('ARCTAN2',across,front_axis)
axial=math('ADD',math('MULTIPLY',forward,.342),math('MULTIPLY',up,.94))
def noise(scale,longscale):
 vector=nodes.new('ShaderNodeCombineXYZ')
 links.new(math('MULTIPLY',math('SINE',angle),scale),vector.inputs['X'])
 links.new(math('MULTIPLY',math('COSINE',angle),scale),vector.inputs['Y'])
 links.new(math('MULTIPLY',axial,longscale),vector.inputs['Z'])
 n=nodes.new('ShaderNodeTexNoise');links.new(vector.outputs[0],n.inputs['Vector']);n.inputs['Scale'].default_value=1;n.inputs['Detail'].default_value=1.3;n.inputs['Roughness'].default_value=.55
 return n.outputs['Fac']
clumps=noise(18,12);strands=noise(85,20);fine=noise(220,24)
height=math('ADD',math('MULTIPLY',clumps,.25),math('ADD',math('MULTIPLY',strands,.6),math('MULTIPLY',fine,.15)))
color_ramp=nodes.new('ShaderNodeValToRGB');color_ramp.color_ramp.elements[0].position=.19;color_ramp.color_ramp.elements[0].color=(.007,.0038,.0026,1)
color_ramp.color_ramp.elements[1].position=.81;color_ramp.color_ramp.elements[1].color=(.033,.020,.0125,1)
links.new(height,color_ramp.inputs[0]);color=mix(oldcolor,color_ramp.outputs[0],math('MULTIPLY',mask,.92));links.new(color,shader.inputs['Base Color'])
bump=nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.00035;links.new(math('MULTIPLY',mask,.7),bump.inputs['Strength']);links.new(height,bump.inputs['Height']);links.new(oldnormal,bump.inputs['Normal']);links.new(bump.outputs[0],shader.inputs['Normal'])
roughnew=math('SUBTRACT',.67,math('MULTIPLY',strands,.18))
rough=math('ADD',math('MULTIPLY',oldrough,math('SUBTRACT',1,mask)),math('MULTIPLY',mask,roughnew))
spec=math('ADD',math('MULTIPLY',oldspec,math('SUBTRACT',1,mask)),math('MULTIPLY',mask,.065))
links.new(rough,shader.inputs['Roughness']);links.new(spec,shader.inputs['Specular IOR Level'])
color.node.label='V38_COLOR';rough.node.label='V38_ROUGHNESS';spec.node.label='V38_SPECULAR_HALF'
scene.cycles.samples=32
for label,location in [('front',(0,-3,1.585)),('quarter',(1.45,-2.62,1.585)),('top',(.1,-2,3))]:
 scene.camera.location=location;scene.camera.rotation_euler=(Vector((0,0,1.585))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(root/f'work/hair38-preview-{label}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/hair38-surface.blend'),compress=True)
(root/'work/hair38-reference-analysis.md').write_text('Frontal portrait: dark brown, fine glossy strands, slightly left-offset curtain part, larger right lobe, tapered overlapping fringe. v37: silhouette broadly close, surface too continuous and cap-like. This pass uses a forward-tilted comb field with nested lock/strand scales and softer broad reflection. Geometry and shared ear/fringe boundaries are retained. Side/back grooming is an inference from the one frontal image. No likeness score is claimed.\n')
