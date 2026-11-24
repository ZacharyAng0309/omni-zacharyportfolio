import json,struct
from pathlib import Path
base=Path(r'D:\omni-workstation\projects\ZacharyPortfolio\public\models')
for name in ['Meshy_AI_Professional_Headshot_1020045352_generate.glb','zachary_textured_v19.glb','Asian_M_3_Busi.glb']:
    path=base/name
    with path.open('rb') as file:
        header=file.read(20);count=struct.unpack_from('<I',header,12)[0];g=json.loads(file.read(count))
    print(name,'bytes',path.stat().st_size,'meshes',len(g.get('meshes',[])),'triangles',sum(g['accessors'][p['indices']]['count']//3 for mesh in g.get('meshes',[]) for p in mesh['primitives'] if 'indices' in p),'images',[(im.get('mimeType'),g['bufferViews'][im['bufferView']]['byteLength']) for im in g.get('images',[]) if 'bufferView' in im])
