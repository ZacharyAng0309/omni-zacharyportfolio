import bpy,heapq
import numpy as np
scene=bpy.context.scene
hair=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith('SM_Character_Hair'))
pos=np.array([v.co[:] for v in hair.data.vertices]); _,inv=np.unique(np.round(pos,6),axis=0,return_inverse=True)
count=inv.max()+1; cp=np.zeros((count,3)); np.add.at(cp,inv,pos); cp/=np.bincount(inv)[:,None]
edges=np.array([(inv[e.vertices[0]],inv[e.vertices[1]]) for e in hair.data.edges]); edges=np.sort(edges,axis=1)
tri=np.array([p.vertices[:] for p in hair.data.polygons]); sides=np.sort(inv[np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]])],axis=1); unique,n=np.unique(sides,axis=0,return_counts=True)
boundary=np.unique(unique[n==1]); adjacency=[[] for _ in range(count)]
for a,b in np.unique(edges,axis=0):
 length=float(np.linalg.norm(cp[a]-cp[b])); adjacency[a].append((b,length)); adjacency[b].append((a,length))
distance=np.full(count,1.0); queue=[]
for a in boundary: distance[a]=0; heapq.heappush(queue,(0,int(a)))
while queue:
 dist,a=heapq.heappop(queue)
 if dist>distance[a]: continue
 for b,length in adjacency[a]:
  nd=dist+length
  if nd<distance[b]: distance[b]=nd; heapq.heappush(queue,(nd,int(b)))
t=np.clip((distance[inv]-0.004)/0.015,0,1); weight=t*t*(3-2*t)
attribute=hair.data.attributes.new('strand_weight','FLOAT','POINT')
attribute.data.foreach_set('value',weight.astype(np.float32))
tree=hair.data.materials[0].node_tree; nodes=tree.nodes; links=tree.links
mix=next(n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MIX')
attr=nodes.new('ShaderNodeAttribute'); attr.attribute_name='strand_weight'
mult=nodes.new('ShaderNodeMath'); mult.operation='MULTIPLY'; mult.inputs[1].default_value=0.45; links.new(attr.outputs['Fac'],mult.inputs[0]); links.new(mult.outputs[0],mix.inputs[0])
mapping=next(n for n in nodes if n.type=='VECT_MATH' and n.operation=='MULTIPLY'); mapping.inputs[1].default_value=(800,800,30)
bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED'); bsdf.inputs['Roughness'].default_value=0.68; bsdf.inputs['Specular IOR Level'].default_value=0.12
bump=next(n for n in nodes if n.type=='BUMP'); bump.inputs['Strength'].default_value=0.20; bump.inputs['Distance'].default_value=0.00015
links.new(mult.outputs[0],bump.inputs['Strength'])
scene.cycles.samples=64
scene.render.filepath=r'C:\Users\ziyan\Documents\Codex\2026-10-30\acc\outputs\avatar-v22-hair-trial-2.png'
bpy.ops.render.render(write_still=True)
print('Feathered detail across',len(boundary),'logical hair boundary vertices')
