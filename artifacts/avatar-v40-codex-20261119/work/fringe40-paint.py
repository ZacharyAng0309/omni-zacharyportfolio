"""Blender surface-clone paint across the authored curtain hairline."""
import bpy,sys,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v39_candidate.glb');p=a.prim('SM_Character_Face');points=a.pos('SM_Character_Face').copy();tri=a.arr(p['indices']).reshape(-1,3).copy();uv=a.arr(p['attributes']['TEXCOORD_1']).copy();bvh=BVHTree.FromPolygons([Vector(x) for x in points],tri.tolist(),all_triangles=True)
scene=bpy.data.scenes['Portrait review v39'];bpy.context.window.scene=scene
face=next(o for o in scene.objects if o.name.startswith('SM_Character_Face'));hair=next(o for o in scene.objects if o.name.startswith('SM_Character_Hair'))
fshader=next(n for n in face.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED');source=fshader.inputs['Base Color'].links[0].from_node.image
source_pixels=np.array(source.pixels[:]).reshape(source.size[1],source.size[0],4)
guides=[(-.09,1.615),(-.075,1.620),(-.060,1.625),(-.045,1.632),(-.033,1.650),(-.025,1.662),(-.020,1.658),(-.012,1.646),(0,1.639),(.015,1.633),(.030,1.629),(.05,1.625),(.065,1.622),(.08,1.617),(.09,1.614)]
def clone_uv(x):
 line=np.interp(x,[q[0] for q in guides],[q[1] for q in guides]);xx=float(np.clip(-.03+x*.08,-.04,-.022));yy=float(np.clip(1.628+(line-1.64)*.08,1.627,1.631))
 hit,normal,index,d=bvh.ray_cast(Vector((xx,yy,.35)),Vector((0,0,-1)));assert hit is not None,(x,xx,yy)
 corners=points[tri[index]];bary=np.linalg.lstsq(np.vstack([corners.T,np.ones(3)]),np.r_[hit[:],1],rcond=None)[0];co=(uv[tri[index]]*bary[:,None]).sum(0);return (co[0],1-co[1])
for obj in [face,hair]:
 material=obj.data.materials[0].copy();obj.data.materials[0]=material;material.name='M_FringeRepair40_'+obj.name;tree=material.node_tree;nodes=tree.nodes;links=tree.links;shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');original=shader.inputs['Base Color'].links[0].from_socket
 original_uv=obj.data.uv_layers[1].name
 for n in list(nodes):
  if n.type=='TEX_IMAGE' and not n.inputs['Vector'].is_linked:
   uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map=original_uv;links.new(uvnode.outputs[0],n.inputs['Vector'])
 clone=obj.data.color_attributes.new(name='ForeheadClone40',type='FLOAT_COLOR',domain='CORNER');cache={}
 for v in obj.data.vertices:
  u,vv=clone_uv(v.co.x);px=np.clip(u*source.size[0]-.5,0,source.size[0]-1);py=np.clip(vv*source.size[1]-.5,0,source.size[1]-1);ix,iy=int(px),int(py);tx,ty=px-ix,py-iy
  rgb=(1-ty)*((1-tx)*source_pixels[iy,ix,:3]+tx*source_pixels[iy,min(ix+1,source.size[0]-1),:3])+ty*((1-tx)*source_pixels[min(iy+1,source.size[1]-1),ix,:3]+tx*source_pixels[min(iy+1,source.size[1]-1),min(ix+1,source.size[0]-1),:3])
  rgb=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)*.86;cache[v.index]=[*rgb,1]
 for loop in obj.data.loops:clone.data[loop.index].color=cache[loop.vertex_index]
 obj.data.uv_layers.active_index=1;obj.data.uv_layers[1].active_render=True
 def math(op,x,y=0):
  n=nodes.new('ShaderNodeMath');n.operation=op
  for socket,val in zip(n.inputs[:2],(x,y)):
   if isinstance(val,(float,int)):socket.default_value=val
   else:links.new(val,socket)
  return n.outputs[0]
 def smooth(value,lo,hi):
  n=nodes.new('ShaderNodeMapRange');n.interpolation_type='SMOOTHSTEP';links.new(value,n.inputs['Value']);n.inputs['From Min'].default_value=lo;n.inputs['From Max'].default_value=hi;return n.outputs[0]
 def mix(x,y,w):
  n=nodes.new('ShaderNodeMixRGB');links.new(w,n.inputs[0]);links.new(x,n.inputs[1]);links.new(y,n.inputs[2]);return n.outputs[0]
 geo=nodes.new('ShaderNodeNewGeometry');xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],xyz.inputs[0]);x=xyz.outputs['X'];up=xyz.outputs['Z'];forward=math('MULTIPLY',xyz.outputs['Y'],-1)
 curve=nodes.new('ShaderNodeFloatCurve');curve.mapping.initialize();curve.mapping.use_clip=False;c=curve.mapping.curves[0]
 c.points[0].location=(0,(guides[0][1]-1.61)/.06);c.points[-1].location=(1,(guides[-1][1]-1.61)/.06)
 for xx,yy in guides[1:-1]:c.points.new((xx+.09)/.18,(yy-1.61)/.06)
 for point in c.points:point.handle_type='AUTO'
 curve.mapping.update();links.new(math('DIVIDE',math('ADD',x,.09),.18),curve.inputs['Value']);line=math('ADD',math('MULTIPLY',curve.outputs['Value'],.06),1.61)
 angle=math('ARCTAN2',math('ADD',x,.014),math('SUBTRACT',math('MULTIPLY',math('ADD',forward,.015),.94),math('MULTIPLY',math('SUBTRACT',up,1.62),.342)))
 axial=math('ADD',math('MULTIPLY',math('ADD',forward,.015),.342),math('MULTIPLY',math('SUBTRACT',up,1.62),.94))
 def noise(scale,longscale):
  vector=nodes.new('ShaderNodeCombineXYZ');links.new(math('MULTIPLY',math('SINE',angle),scale),vector.inputs[0]);links.new(math('MULTIPLY',math('COSINE',angle),scale),vector.inputs[1]);links.new(math('MULTIPLY',axial,longscale),vector.inputs[2]);n=nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=1;n.inputs['Detail'].default_value=1.3;n.inputs['Roughness'].default_value=.55;links.new(vector.outputs[0],n.inputs['Vector']);return n.outputs['Fac']
 clumps=noise(18,12);strands=noise(85,20);fine=noise(220,24);height=math('ADD',math('MULTIPLY',clumps,.25),math('ADD',math('MULTIPLY',strands,.6),math('MULTIPLY',fine,.15)))
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.19;ramp.color_ramp.elements[0].color=(.007,.0038,.0026,1);ramp.color_ramp.elements[1].position=.81;ramp.color_ramp.elements[1].color=(.033,.020,.0125,1);links.new(height,ramp.inputs[0])
 skin=nodes.new('ShaderNodeAttribute');skin.attribute_name=clone.name
 distance=math('SUBTRACT',up,line);flowdistance=math('ADD',distance,math('MULTIPLY',math('SUBTRACT',clumps,.5),.008));core=smooth(flowdistance,0,.003);filaments=smooth(fine,.38,.62);tips=math('MULTIPLY',filaments,smooth(flowdistance,-.006,.002));is_hair=math('MAXIMUM',core,tips)
 # Preserve the photographed wisps and skin. Harmonize the mismatched hair color
 # across the two material domains instead of replacing the strand outline.
 channels=nodes.new('ShaderNodeSeparateColor');links.new(original,channels.inputs[0]);painted_hair=math('SUBTRACT',1,smooth(channels.outputs['Red'],.10,.28));coverage=math('MAXIMUM',painted_hair,smooth(distance,.003,.012))
 band=math('MULTIPLY',smooth(distance,-.022,-.010),math('SUBTRACT',1,smooth(distance,.030,.045)));band=math('MULTIPLY',band,smooth(up,1.620,1.626));band=math('MULTIPLY',band,smooth(forward,.055,.080));band=math('MULTIPLY',band,math('SUBTRACT',1,smooth(math('ABSOLUTE',x),.062,.082)))
 strength=math('MULTIPLY',band,coverage);result=mix(original,ramp.outputs['Color'],strength);links.new(result,shader.inputs['Base Color']);strength.node.label='REPAIR40_MASK';ramp.label='REPAIR40_PAINT'
scene.cycles.samples=32
for label,location in [('front',(0,-3,1.585)),('quarter',(1.45,-2.62,1.585))]:
 scene.camera.location=location;scene.camera.rotation_euler=(Vector((0,0,1.585))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(root/f'work/fringe40-preview-{label}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/fringe40-paint.blend'),compress=True)
(root/'work/fringe40-guides.json').write_text(json.dumps({'guides_x_y_m':guides,'band_lower_fade_m':[-.022,-.010],'band_upper_fade_m':[.030,.045],'outer_lateral_m':.082,'brow_protection_fade_y_m':[1.620,1.626],'method':'native Blender material painting harmonizes original hair pixels across Face/Hair with the v38 curtain strand field; source skin and photographed wisps retained'},indent=2))
