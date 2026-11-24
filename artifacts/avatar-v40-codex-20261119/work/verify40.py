from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,io,copy
from glb_asset import Asset
root=Path(__file__).resolve().parents[1];b=Asset(root/'outputs/zachary_character_v39_candidate.glb');shape=Asset(root/'work/fringe40-shape.glb');a=Asset(root/'outputs/zachary_character_v40_candidate.glb');patch=np.load(root/'work/fringe40-patch-uv.npz');mapping=json.loads((root/'work/fringe40-vertex-mapping.json').read_text());bake=json.loads((root/'work/fringe40-patch-bake.json').read_text());checks=[];metrics={}
def check(label,value):
 checks.append({'check':label,'passed':bool(value)});assert value,label
def payload(asset,i):
 v=asset.g['bufferViews'][asset.g['images'][i]['bufferView']];return asset.bin[v['byteOffset']:v['byteOffset']+v['byteLength']]
def pixels(asset,i):return np.array(Image.open(io.BytesIO(payload(asset,i))).convert('RGB')).astype(float)
def sample(image,uv):
 x=np.clip(uv[:,0]*image.shape[1]-.5,0,image.shape[1]-1);y=np.clip(uv[:,1]*image.shape[0]-.5,0,image.shape[0]-1);ix=x.astype(int);iy=y.astype(int);tx=(x-ix)[:,None];ty=(y-iy)[:,None];jx=np.minimum(ix+1,image.shape[1]-1);jy=np.minimum(iy+1,image.shape[0]-1)
 return (1-ty)*((1-tx)*image[iy,ix]+tx*image[iy,jx])+ty*((1-tx)*image[jy,ix]+tx*image[jy,jx])
changed=set();totalverts=0
for mi,(name,label,image_index) in enumerate([('SM_Character_Face','face',5),('SM_Character_Hair','hair',1)]):
 old=b.prim(name);expected=shape.prim(name);new=a.prim(name);ot=shape.arr(expected['indices']).reshape(-1,3);nt=a.arr(new['indices']).reshape(-1,3);sources=np.array(mapping[label]['sources']);totalverts+=len(sources);changed.update(old['attributes'].values());changed.add(old['indices'])
 for t in old.get('targets',[]):changed.update(t.values())
 check(name+' triangle count preserved',len(ot)==len(nt));check(name+' UV2 exists','TEXCOORD_2' in new['attributes'])
 for semantic,index in expected['attributes'].items():check(name+' per-corner '+semantic+' preserved',np.array_equal(a.arr(new['attributes'][semantic])[nt],shape.arr(index)[ot]))
 for k,(target,original) in enumerate(zip(new.get('targets',[]),expected.get('targets',[]))):
  for semantic,index in original.items():check(f'{name} target {k} {semantic} copied exactly',np.array_equal(a.arr(target[semantic])[nt],shape.arr(index)[ot]))
 check(name+' copied joint weights normalized',np.max(abs(a.arr(new['attributes']['WEIGHTS_0']).sum(1)-1))<1e-5)
 uv=a.arr(new['attributes']['TEXCOORD_2']);rows=np.where(patch['source_mesh']==mi)[0]
 for row in rows:
  tid=int(patch['source_triangle'][row]);check(f'{label} patch triangle {tid} corner mapping',np.max(abs(uv[nt[tid]]-patch[label][row]))<1e-6)
 oldimage=pixels(b,image_index);newimage=pixels(a,image_index);x,y,w,h=bake[label]['rectangle_pixels'];occupancy=Image.new('L',(oldimage.shape[1],oldimage.shape[0]));draw=ImageDraw.Draw(occupancy);originaluv=b.arr(old['attributes']['TEXCOORD_1']);oldtri=b.arr(old['indices']).reshape(-1,3)
 for triangle in oldtri:draw.polygon([tuple(v) for v in originaluv[triangle]*[oldimage.shape[1],oldimage.shape[0]]],fill=255)
 check(label+' atlas slot was unused',not np.any(np.asarray(occupancy)[y:y+h,x:x+w]))
 unpatched=np.setdiff1d(np.arange(len(ot)),patch['source_triangle'][rows]);beforeuv=originaluv[oldtri[unpatched]].mean(1);afteruv=uv[nt[unpatched]].mean(1);difference=np.abs(sample(newimage,afteruv)-sample(oldimage,beforeuv))
 metrics[label+'_unchanged_surface_color_error_255']={'sampled_triangles':len(unpatched),'mean':float(difference.mean()),'p99':float(np.percentile(difference,99))};check(label+' unchanged surface average color retained',difference.mean()<2.5);check(label+' unchanged surface p99 color retained',np.percentile(difference,99)<12)
 changedpos=shape.pos(name)-b.pos(name);check(name+' local movement below 2.001 mm',np.linalg.norm(changedpos,axis=1).max()<.002001)
 for key in ['pbrMetallicRoughness','normalTexture','extensions']:
  om=copy.deepcopy(b.g['materials'][old['material']].get(key));nm=copy.deepcopy(a.g['materials'][new['material']].get(key))
  if key=='pbrMetallicRoughness':nm['baseColorTexture']['texCoord']=om['baseColorTexture']['texCoord']
  check(name+' material '+key+' preserved',om==nm)
 check(name+' base color selects UV2',a.g['materials'][new['material']]['pbrMetallicRoughness']['baseColorTexture']['texCoord']==2)
for i in range(len(b.g['accessors'])):
 check(f'Accessor {i} finite',np.isfinite(a.arr(i)).all())
 if i not in changed:check(f'Accessor {i} byte preserved',np.array_equal(a.arr(i),b.arr(i)))
for key in ['nodes','skins','scenes','scene','textures','samplers','animations','extensionsUsed','extensionsRequired']:check(key+' unchanged',a.g.get(key)==b.g.get(key))
for i in range(len(a.g['images'])):
 check(f'Image {i} under 100 KB',len(payload(a,i))<100000)
 if i not in [1,5]:check(f'Image {i} byte preserved',payload(a,i)==payload(b,i))
for name in ['SM_Character_Face','SM_Character_Hair']:
 p=shape.prim(name);x=shape.pos(name);old=b.pos(name);t=shape.arr(p['indices']).reshape(-1,3);oc=np.cross(old[t[:,1]]-old[t[:,0]],old[t[:,2]]-old[t[:,0]]);nc=np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]]);oa=np.linalg.norm(oc,axis=1);na=np.linalg.norm(nc,axis=1)
 affected=np.any(np.linalg.norm(x-old,axis=1)[t]>1e-8,axis=1)
 check(name+' moved triangle orientation valid',np.min((np.sum(oc*nc,axis=1)/np.maximum(oa*na,1e-30))[affected])>.8);check(name+' moved triangle area valid',np.min((na/np.maximum(oa,1e-30))[affected])>.65)
fp=b.prim('SM_Character_Face');moving=np.max(np.stack([np.linalg.norm(b.arr(t['POSITION']),axis=1) for t in fp['targets']]),axis=0)>1e-7
check('Every moving facial vertex base preserved',np.array_equal(shape.pos('SM_Character_Face')[moving],b.pos('SM_Character_Face')[moving]))
old=b.pos('SM_Character_Hair');hm={tuple(np.rint(v.astype(float)*1e6).astype('i8')):j for j,v in enumerate(old)};pairs=[(i,hm[tuple(np.rint(v.astype(float)*1e6).astype('i8'))]) for i,v in enumerate(b.pos('SM_Character_Face')) if tuple(np.rint(v.astype(float)*1e6).astype('i8')) in hm]
check('135 shared face/hair pairs coincident',len(pairs)==135 and max(np.linalg.norm(shape.pos('SM_Character_Face')[i]-shape.pos('SM_Character_Hair')[j]) for i,j in pairs)<1e-6)
# Pixel-centre coverage audit of the local unwrap; a finite sampled overlap check.
coverage=np.zeros((512,512),dtype='u2')
for uv in patch['local_uv']:
 q=uv*511;lo=np.maximum(np.floor(q.min(0)).astype(int),0);hi=np.minimum(np.ceil(q.max(0)).astype(int),511);xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);v0=q[1]-q[0];v1=q[2]-q[0];det=v0[0]*v1[1]-v0[1]*v1[0]
 if abs(det)<1e-10:continue
 dx=xx-q[0,0];dy=yy-q[0,1];u=(dx*v1[1]-dy*v1[0])/det;v=(v0[0]*dy-v0[1]*dx)/det;inside=(u>1e-6)&(v>1e-6)&(u+v<1-1e-6);coverage[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=inside.astype('u2')
metrics['unwrap_overlap_texel_centres']=int((coverage>1).sum());check('Dedicated unwrap sampled without overlaps',metrics['unwrap_overlap_texel_centres']==0)
triangles=sum(a.arr(p['indices']).size//3 for mesh in a.g['meshes'] for p in mesh['primitives']);metrics.update(triangles=triangles,glb_bytes=a.path.stat().st_size,joints=len(a.g['skins'][0]['joints']),new_uv_vertex_copies=sum(len(mapping[k]['sources'])-len(b.pos(n)) for k,n in [('face','SM_Character_Face'),('hair','SM_Character_Hair')]))
check('Triangle budget retained',triangles==44910);check('GLB below 3 MB',a.path.stat().st_size<3000000);check('52 joints retained',metrics['joints']==52)
report={'checks_passed':len(checks),'checks_failed':0,'metrics':metrics,'checks':checks};(root/'work/fringe40-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
