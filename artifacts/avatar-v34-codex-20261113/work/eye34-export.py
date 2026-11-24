import sys,json,copy,io
from pathlib import Path
from collections import defaultdict,Counter,deque
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v33_candidate.glb');p=a.prim('SM_Character_Face');arrays={k:a.arr(i).copy() for k,i in p['attributes'].items()};old_n=len(arrays['POSITION']);targets=[a.arr(t['POSITION']).copy() for t in p['targets']]
r=np.load(root/'work/eye34-baked-data.npz');points=r['points'];tri=r['triangles'];source_ids=r['source_ids'];uv=r['uv'].copy();uv[:,:,1]=1-uv[:,:,1];new_normals=r['normals'];patched=r['patched']
# Keep the original face layout intact in the left atlas half. Only repaired
# triangles use the baked eye layout in the right half, preventing overlaps
# from the experimental whole-face unwrap reaching nose/lip triangles.
geo_keys={tuple(np.rint(v.astype(float)*1e6).astype('i8')):i for i,v in enumerate(points)}
old_geo=np.array([geo_keys[tuple(np.rint(v.astype(float)*1e6).astype('i8'))] for v in arrays['POSITION']])
old_tri=a.arr(p['indices']).reshape(-1,3).copy()
old_lookup={tuple(sorted(old_geo[t])):t for t in old_tri}
for j,t in enumerate(tri):
 if patched[j]:uv[j,:,0]=uv[j,:,0]*.5+.5
 else:
  source=old_lookup[tuple(sorted(t))];mapping={old_geo[i]:i for i in source}
  uv[j]=arrays['TEXCOORD_0'][[mapping[i] for i in t]];uv[j,:,0]*=.5
def key(x):return tuple(np.rint(np.asarray(x,dtype=float)*1e6).astype('i8'))
pool=defaultdict(list)
for i,x in enumerate(arrays['POSITION']):pool[key(x)].append(i)
edges=Counter(tuple(sorted((int(a),int(b)))) for face in tri[patched] for a,b in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]);patch_vertices=set(int(i) for i in tri[patched].ravel());boundary={i for e,n in edges.items() if n==1 for i in e};adj=defaultdict(set)
for e in edges:
 adj[e[0]].add(e[1]);adj[e[1]].add(e[0])
distance={i:0 for i in boundary};queue=deque(boundary)
while queue:
 i=queue.popleft()
 for j in adj[i]:
  if j not in distance:distance[j]=distance[i]+1;queue.append(j)
changed=0
for geo in patch_vertices:
 weight=min(distance.get(geo,0)/3,1)
 if weight==0:continue
 for i in pool[key(points[geo])]:
  n=arrays['NORMAL'][i]*(1-weight)+new_normals[geo]*weight;n/=np.linalg.norm(n)
  if np.linalg.norm(n-arrays['NORMAL'][i])>1e-6:changed+=1
  arrays['NORMAL'][i]=n
rows={k:[v.copy() for v in values] for k,values in arrays.items()};target_rows=[[v.copy() for v in values] for values in targets]
uv1=[np.zeros(2) for _ in range(old_n)];lookup={};assigned=set();new_tri=[];duplicate_sources=[]
for indices,coords in zip(tri,uv):
 row=[]
 for geo,tex in zip(indices,coords):
  signature=(int(geo),tuple(np.rint(tex*1e7).astype('i8')))
  if signature not in lookup:
   choices=pool[key(points[geo])];index=next((i for i in choices if i not in assigned),None)
   if index is None:
    origin=int(source_ids[geo]);index=len(rows['POSITION'])
    for name in rows:rows[name].append(arrays[name][origin].copy())
    for k,target in enumerate(target_rows):target.append(targets[k][origin].copy())
    uv1.append(tex.copy());duplicate_sources.append(origin)
   else:uv1[index]=tex.copy()
   lookup[signature]=index;assigned.add(index)
  row.append(lookup[signature])
 new_tri.append(row)
def append(values,kind,component=5126,target=34962):
 ar=np.asarray(values,dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[component]);a.bin.extend(b'\0'*((-len(a.bin))%4));start=len(a.bin);a.bin.extend(ar.tobytes());vi=len(a.g['bufferViews']);a.g['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':ar.nbytes,'target':target});ai=len(a.g['accessors']);acc={'bufferView':vi,'componentType':component,'type':kind,'count':len(ar)}
 if kind=='VEC3':acc.update(min=ar.min(0).tolist(),max=ar.max(0).tolist())
 a.g['accessors'].append(acc);return ai
def replace(index,values,target=34962):
 old=a.g['accessors'][index];append(values,old['type'],old['componentType'],target);a.g['accessors'][index]=a.g['accessors'].pop()
for name,index in p['attributes'].items():replace(index,rows[name])
for k,target in enumerate(p['targets']):replace(target['POSITION'],target_rows[k])
replace(p['indices'],np.array(new_tri).reshape(-1,1),34963)
p['attributes']['TEXCOORD_1']=append(uv1,'VEC2')
material=a.g['materials'][p['material']];source_texture=a.g['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]
source_image=a.g['images'][source_texture['source']];v=a.g['bufferViews'][source_image['bufferView']];start=v.get('byteOffset',0)
original=Image.open(io.BytesIO(a.bin[start:start+v['byteLength']])).convert('RGB')
eye=Image.open(root/'work/eye34-albedo.png').convert('RGB')
image=Image.new('RGB',(4096,2048));image.paste(original.resize((2048,2048)),(0,0));image.paste(eye,(2048,0))
for quality in range(95,19,-5):
 stream=io.BytesIO();image.save(stream,format='WEBP',quality=quality,method=6);payload=stream.getvalue()
 if len(payload)<100000:break
assert len(payload)<100000
a.bin.extend(b'\0'*((-len(a.bin))%4));offset=len(a.bin);a.bin.extend(payload);view=len(a.g['bufferViews']);a.g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(payload)})
image_index=len(a.g['images']);a.g['images'].append({'bufferView':view,'mimeType':'image/webp','name':'T_Face_v34_Albedo'})
material=a.g['materials'][p['material']];old_texture=material['pbrMetallicRoughness']['baseColorTexture']['index'];texture=copy.deepcopy(a.g['textures'][old_texture]);texture['source']=image_index
if 'EXT_texture_webp' in texture.get('extensions',{}):texture['extensions']['EXT_texture_webp']['source']=image_index
texture_index=len(a.g['textures']);a.g['textures'].append(texture);material['pbrMetallicRoughness']['baseColorTexture']={'index':texture_index,'texCoord':1}
material['pbrMetallicRoughness'].pop('metallicRoughnessTexture',None);material['pbrMetallicRoughness']['roughnessFactor']=.65
material.setdefault('extensions',{}).setdefault('KHR_materials_specular',{}).pop('specularTexture',None);material['extensions']['KHR_materials_specular']['specularFactor']=.35
# Remove historical unused buffer views, retaining accessor indices and all live bytes.
used=sorted({v['bufferView'] for v in a.g['accessors']}|{v['bufferView'] for v in a.g['images']});mapping={old:new for new,old in enumerate(used)};new_bin=bytearray();new_views=[]
for old in used:
 view=copy.deepcopy(a.g['bufferViews'][old]);start=view.get('byteOffset',0);size=view['byteLength'];new_bin.extend(b'\0'*((-len(new_bin))%4));view['byteOffset']=len(new_bin);new_bin.extend(a.bin[start:start+size]);new_views.append(view)
for item in a.g['accessors']+a.g['images']:item['bufferView']=mapping[item['bufferView']]
a.g['bufferViews']=new_views;new_bin.extend(b'\0'*((-len(new_bin))%4));a.bin=new_bin;a.g['buffers'][0]['byteLength']=len(new_bin)
a.save(root/'outputs/zachary_character_v34_candidate.glb')
np.save(root/'work/eye34-duplicate-sources.npy',duplicate_sources)
report={'original_face_vertices':old_n,'final_face_vertices':len(uv1),'added_uv_seam_duplicates':len(duplicate_sources),'changed_normal_copies':changed,'face_triangles':len(new_tri),'baked_texture_bytes':len(payload),'baked_texture_resolution':image.size,'webp_quality':quality,'glb_bytes':(root/'outputs/zachary_character_v34_candidate.glb').stat().st_size,'positions_and_existing_expression_values':'preserved; added vertices duplicate original values','roughness':.65,'specular_factor':.35}
(root/'work/eye34-changes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
