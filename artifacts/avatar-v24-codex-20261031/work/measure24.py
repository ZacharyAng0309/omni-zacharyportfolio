from glb_asset import *
from pathlib import Path
r=Path(__file__).resolve().parents[1]
stats={}
for version in [23,24]:
 a=Asset(r/f'outputs/zachary_character_v{version}_candidate.glb')
 p=a.pos('SM_Character_Face');tri=p[a.arr(a.prim('SM_Character_Face')['indices']).reshape(-1,3)]
 rows=[]
 for h in np.arange(1.578,1.5991,.00025):
  hits=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   u,v=tri[:,i],tri[:,j];mask=(u[:,1]-h)*(v[:,1]-h)<0;u,v=u[mask],v[mask]
   hits.extend(u+((h-u[:,1])/(v[:,1]-u[:,1]))[:,None]*(v-u))
  q=np.array(hits);q=q[(q[:,2]>-.04)&(q[:,2]<.006)];rows.append([-q[:,0].min(),q[:,0].max()])
 widths=np.array(rows)
 chord=np.linspace(widths[0],widths[-1],len(rows))
 stats[version]={'front_rim_max_inward_deviation_mm':np.round(np.maximum(0,chord-widths).max(axis=0)*1000,2).tolist()}
print(stats)
(r/'work/ear24-contour.json').write_text(json.dumps(stats,indent=2))
