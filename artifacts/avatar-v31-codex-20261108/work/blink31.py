"""Constrain blink deformation to the eyelid aperture, protecting brows/hairline."""
from pathlib import Path
import numpy as np,json
from glb_asset import Asset
root=Path(__file__).resolve().parents[1]
asset=Asset(root/'outputs/zachary_character_v30_candidate.glb')
primitive=asset.prim('SM_Character_Face');points=asset.pos('SM_Character_Face')
x,height,depth=points.T
def smooth(a,b,value):
    t=np.clip((value-a)/(b-a),0,1);return t*t*(3-2*t)
report={}
for name,target_index,center in [('eyeBlinkLeft',4,.034),('eyeBlinkRight',5,-.034)]:
    index=primitive['targets'][target_index]['POSITION'];delta=asset.arr(index);old=delta.copy()
    lateral=1-smooth(.012,.025,np.abs(x-center))
    distance=np.abs(height-1.598)
    vertical=np.where(height>=1.598,1-smooth(.007,.014,distance),1-smooth(.007,.022,distance))
    front=smooth(.045,.075,depth)
    delta[:]=0;delta[:,1]=-.97*(height-1.598)*lateral*vertical*front
    asset.g['accessors'][index]['min']=delta.min(axis=0).tolist()
    asset.g['accessors'][index]['max']=delta.max(axis=0).tolist()
    upper=height>=1.612
    assert np.max(np.linalg.norm(delta[upper],axis=1))==0
    report[name]={'changed_vertices':int(np.sum(np.any(delta!=old,axis=1))),
                  'affected_vertices_before':int(np.sum(np.linalg.norm(old,axis=1)>1e-7)),
                  'affected_vertices_after':int(np.sum(np.linalg.norm(delta,axis=1)>1e-7)),
                  'protected_upper_region_old_displacement_mm':float(np.linalg.norm(old[upper],axis=1).max()*1000),
                  'protected_upper_region_new_displacement_mm':0.0}
asset.save(root/'outputs/zachary_character_v31_candidate.glb')
(root/'work/blink31-changes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
