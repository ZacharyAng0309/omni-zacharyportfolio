from glb_asset import *
import hashlib
r=Path(__file__).resolve().parents[1];paths=[r/'outputs'/f'zachary_character_v{n}_candidate.glb' for n in [22,23]];a,b=map(Asset,paths)
check={}
def equal(k,test):check[k]=bool(test);assert test,k
equal('reference file matches shared v22',a.raw==(Path(r'D:\omni-workstation\projects\ZacharyPortfolio\artifacts\avatar-v22-codex-20261030\outputs')/paths[0].name).read_bytes())
for key in ['nodes','skins','meshes','textures','images','materials','scenes']:equal(key+' unchanged',a.g[key]==b.g[key])
allowed=set(); measures={}
for ma,mb in zip(a.g['meshes'],b.g['meshes']):
 for pi,(p,q) in enumerate(zip(ma['primitives'],mb['primitives'])):
  name=ma['name']; pts=b.arr(q['attributes']['POSITION']); old=a.arr(p['attributes']['POSITION']); nn=b.arr(q['attributes']['NORMAL']); inds=b.arr(q['indices']).reshape(-1,3)
  equal(name+str(pi)+' finite vertices and valid indices',np.isfinite(pts).all() and inds.max()<len(pts))
  equal(name+str(pi)+' unit normals',abs(np.linalg.norm(nn,axis=1)-1).max()<.002)
  if name in ['SM_Character_Face','SM_Character_Hair'] or (name=='Sovereign_Titanium_Spectacles' and pi<2):allowed.update([q['attributes']['POSITION'],q['attributes']['NORMAL']])
  if name in ['SM_Character_Face','SM_Character_Hair']:
   oldtri=old[inds];newtri=pts[inds];moved=np.linalg.norm(newtri-oldtri,axis=2).max(axis=1)>.0001
   no=np.cross(oldtri[:,1]-oldtri[:,0],oldtri[:,2]-oldtri[:,0]);newno=np.cross(newtri[:,1]-newtri[:,0],newtri[:,2]-newtri[:,0]);cos=(no*newno).sum(1)/np.maximum(1e-20,np.linalg.norm(no,axis=1)*np.linalg.norm(newno,axis=1))
   measures[name]={'changed_triangles':int(moved.sum()),'normal_rotations_over_90deg':int((cos[moved]<0).sum()),'max_changed_edge_mm':round(float(max(np.linalg.norm(newtri[moved,i]-newtri[moved,(i+1)%3],axis=1).max() for i in range(3)))*1000,2)}
for i in range(len(a.g['accessors'])):
 if i not in allowed:equal('unchanged accessor '+str(i),np.array_equal(a.arr(i),b.arr(i)))
for i,im in enumerate(a.g['images']):
 v=a.g['bufferViews'][im['bufferView']];j=v['byteOffset'];k=j+v['byteLength'];equal('unchanged embedded image '+str(i),a.bin[j:k]==b.bin[j:k])
equal('below 3MB',len(b.raw)<3000000)
report={'checks_passed':sum(check.values()),'triangle_shape_diagnostics':measures,'glb_bytes':len(b.raw),'checks':check}
(r/'work/fit23-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
