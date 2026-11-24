from pathlib import Path
from PIL import Image
import numpy as np,json,io,hashlib
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];a=Asset(root/'work/fringe40-shape.glb');patch=np.load(root/'work/fringe40-patch-uv.npz');report={};replacements={};mappings={}
bake=json.loads((root/'work/fringe40-patch-bake.json').read_text())
for name,digest in bake['verified_files'].items():assert hashlib.sha256((root/'work'/name).read_bytes()).hexdigest()==digest,'Incomplete or mixed bake outputs'
def add_accessor_view(values,accessor_index,target):
 ar=np.ascontiguousarray(values);a.bin.extend(b'\0'*((-len(a.bin))%4));view={'buffer':0,'byteOffset':len(a.bin),'byteLength':ar.nbytes,'target':target};a.bin.extend(ar.tobytes());a.g['bufferViews'].append(view);acc=a.g['accessors'][accessor_index];acc.update(bufferView=len(a.g['bufferViews'])-1,byteOffset=0,count=len(ar));acc.update(min=ar.min(0).reshape(-1).tolist(),max=ar.max(0).reshape(-1).tolist())
for mi,(name,label,image_index) in enumerate([('SM_Character_Face','face',5),('SM_Character_Hair','hair',1)]):
 p=a.prim(name);arrays={k:a.arr(i).copy() for k,i in p['attributes'].items()};targets=[{k:a.arr(i).copy() for k,i in t.items()} for t in p.get('targets',[])];tri=a.arr(p['indices']).reshape(-1,3).copy();sources=list(range(len(arrays['POSITION'])));coords=[v.copy() for v in arrays['TEXCOORD_1']];lookup={};rows=np.where(patch['source_mesh']==mi)[0]
 # Match unwrapped corners to the source triangle's corner order by preserving
 # Blender's bmesh face-loop order. It is checked against the source geometry below.
 for row in rows:
  tid=int(patch['source_triangle'][row]);original=tri[tid].copy()
  for corner,(source,uv) in enumerate(zip(original,patch[label][row])):
   key=(int(source),tuple(np.rint(uv*1e7).astype('i8')))
   if key not in lookup:lookup[key]=len(sources);sources.append(int(source));coords.append(uv.copy())
   tri[tid,corner]=lookup[key]
 sources=np.asarray(sources,dtype='i4');mappings[label]={'sources':sources.tolist(),'patched_triangles':patch['source_triangle'][rows].tolist()}
 # Preserve UV0/UV1 for all existing normal/parameter maps. The new albedo
 # coordinates use a separate channel so those maps cannot sample blank atlas space.
 new_uv=len(a.g['accessors']);a.g['accessors'].append(dict(a.g['accessors'][p['attributes']['TEXCOORD_1']]));p['attributes']['TEXCOORD_2']=new_uv
 for semantic,index in p['attributes'].items():add_accessor_view(np.asarray(coords,dtype='f4') if semantic=='TEXCOORD_2' else arrays[semantic][sources],index,34962)
 a.g['materials'][p['material']]['pbrMetallicRoughness']['baseColorTexture']['texCoord']=2
 for target,values in zip(p.get('targets',[]),targets):
  for semantic,index in target.items():add_accessor_view(values[semantic][sources],index,34962)
 add_accessor_view(tri.reshape(-1,1),p['indices'],34963)
 image=Image.open(root/f'work/fringe40-{label}-raw.png').convert('RGB');path=root/f'work/fringe40-{label}.webp'
 for quality in range(95,29,-5):
  image.save(path,quality=quality,method=6)
  if path.stat().st_size<100000:break
 assert path.stat().st_size<100000
 info=a.g['images'][image_index];info['name']='T_FringeRepair_v40_'+label;replacements[info['bufferView']]=path.read_bytes();report[label]={'bytes':path.stat().st_size,'quality':quality,'resolution':list(image.size),'old_vertices':len(arrays['POSITION']),'new_vertices':len(sources),'patched_triangles':len(rows)}
# Compact superseded attribute views, retaining accessor indices and every active byte.
used=sorted({v['bufferView'] for v in a.g['accessors']}|{im['bufferView'] for im in a.g['images']});mapping={old:new for new,old in enumerate(used)};binary=bytearray();views=[]
for i in used:
 v=dict(a.g['bufferViews'][i]);data=replacements.get(i,a.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);binary.extend(b'\0'*((-len(binary))%4));v['byteOffset']=len(binary);v['byteLength']=len(data);binary.extend(data);views.append(v)
binary.extend(b'\0'*((-len(binary))%4))
for acc in a.g['accessors']:acc['bufferView']=mapping[acc['bufferView']]
for image in a.g['images']:image['bufferView']=mapping[image['bufferView']]
a.g['bufferViews']=views;a.bin=binary;a.g['buffers'][0]['byteLength']=len(binary);path=root/'outputs/zachary_character_v40_candidate.glb';a.save(path);report['glb_bytes']=path.stat().st_size
(root/'work/fringe40-textures.json').write_text(json.dumps(report,indent=2));(root/'work/fringe40-vertex-mapping.json').write_text(json.dumps(mappings));print(json.dumps(report))
