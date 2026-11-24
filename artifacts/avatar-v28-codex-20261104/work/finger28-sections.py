"""Measure connected cross-sections through the existing finger surfaces."""
from pathlib import Path
import numpy as np, json
from glb_asset import Asset
root=Path(__file__).resolve().parents[1]
asset=Asset(root/'outputs/zachary_character_v27_candidate.glb')
prim=asset.prim('SM_Character_Hands'); points=asset.pos('SM_Character_Hands')
triangles=asset.arr(prim['indices']).reshape(-1,3)
rows={}
for side in ['Right','Left']:
    sign=-1 if side=='Right' else 1
    tris=triangles[np.mean(points[triangles][:,:,0],axis=1)*sign>0]
    result=[]
    for y in np.arange(.75,.876,.005):
        segments=[]
        for tri in points[tris]:
            d=tri[:,1]-y
            hits=[]
            for a,b in [(0,1),(1,2),(2,0)]:
                if d[a]*d[b]<0: hits.append(tri[a]+(tri[b]-tri[a])*d[a]/(d[a]-d[b]))
            if len(hits)==2: segments.append(hits)
        links={}; coords={}
        for a,b in segments:
            ka,kb=tuple(np.round(a,6)),tuple(np.round(b,6))
            links.setdefault(ka,set()).add(kb); links.setdefault(kb,set()).add(ka)
            coords[ka]=a; coords[kb]=b
        visited=set(); loops=[]
        for key in links:
            if key in visited: continue
            todo=[key]; component=[]
            while todo:
                k=todo.pop()
                if k in visited: continue
                visited.add(k); component.append(k); todo.extend(links[k]-visited)
            if len(component)<3: continue
            selected=set(component)
            ss=[(a,b) for a,b in segments if tuple(np.round(a,6)) in selected]
            lengths=np.array([np.linalg.norm(a-b) for a,b in ss])
            center=np.average([(a+b)/2 for a,b in ss],weights=lengths,axis=0)
            loops.append({'center':center.tolist(),'perimeter':float(lengths.sum()),'segments':len(ss),'closed':all(len(links[k])==2 for k in component)})
        loops.sort(key=lambda l:l['center'][2],reverse=True)
        result.append({'y':round(float(y),4),'loops':loops})
    rows[side]=result
(root/'work/finger28-sections.json').write_text(json.dumps(rows,indent=2))
for side,data in rows.items():
    print(side)
    for row in data:
        print(row['y'],[(np.round(l['center'],4).tolist(),round(l['perimeter']*1000,1),l['closed']) for l in row['loops']])
