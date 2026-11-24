"""Add modest oral anatomy using native Blender bmesh primitives.
The visible dental form is an artistic approximation, not photo-derived anatomy.
Original v32 buffers, meshes and morphs are left unchanged.
"""
import bpy,bmesh,sys,json,copy,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
a=Asset(root/'outputs/zachary_character_v32_candidate.glb')
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
face_mesh=next(i for i,m in enumerate(a.g['meshes']) if m['name']=='SM_Character_Face')
face_node=next(i for i,n in enumerate(a.g['nodes']) if n.get('mesh')==face_mesh)
head_node=next(i for i,n in enumerate(a.g['nodes']) if n.get('name')=='Head')
head_joint=a.g['skins'][a.g['nodes'][face_node]['skin']]['joints'].index(head_node)
target_names=a.g['meshes'][face_mesh]['extras']['targetNames']
def accessor(values,kind,component=5126,target=34962):
    ar=np.asarray(values,dtype={5123:'<u2',5126:'<f4'}[component])
    a.bin.extend(b'\0'*((-len(a.bin))%4));offset=len(a.bin);a.bin.extend(ar.tobytes())
    view=len(a.g['bufferViews']);a.g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':ar.nbytes,'target':target})
    index=len(a.g['accessors']);item={'bufferView':view,'componentType':component,'count':len(ar),'type':kind}
    if kind=='VEC3':item.update(min=ar.min(0).tolist(),max=ar.max(0).tolist())
    a.g['accessors'].append(item);return index
def material(name,color,roughness,specular):
    index=len(a.g['materials']);a.g['materials'].append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':[*color,1],'metallicFactor':0,'roughnessFactor':roughness},'extensions':{'KHR_materials_specular':{'specularFactor':specular}},'doubleSided':False});return index
enamel=material('Zachary_Enamel',(.64,.60,.50),.30,.35)
tissue=material('Zachary_Tongue',(.30,.065,.080),.52,.20)
reports=[]
def finish(name,bm,material_index,lower=False,mouth_drop=0):
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.normal_update()
    mesh=bpy.data.meshes.new(name);bm.to_mesh(mesh);bm.free();mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj)
    points=np.array([v.co[:] for v in mesh.vertices],dtype=float);normals=np.array([v.normal[:] for v in mesh.vertices]);tri=np.array([p.vertices[:] for p in mesh.polygons],dtype=int)
    n=len(points);joints=np.zeros((n,4),dtype='u2');joints[:,0]=head_joint;weights=np.zeros((n,4));weights[:,0]=1
    attributes={'POSITION':accessor(points,'VEC3'),'NORMAL':accessor(normals,'VEC3'),'JOINTS_0':accessor(joints,'VEC4',5123),'WEIGHTS_0':accessor(weights,'VEC4')}
    morphs=[np.zeros_like(points) for _ in target_names]
    if lower:
        hinge=np.array([0,1.550,.012]);angle=.13
        rotation=np.array([[1,0,0],[0,math.cos(angle),-math.sin(angle)],[0,math.sin(angle),math.cos(angle)]])
        morphs[2][:]=[0,-mouth_drop,-.001]
        morphs[3]=(points-hinge)@rotation.T+hinge-points
        morphs[7]=morphs[2]*.85+morphs[3]*.55
    targets=[{'POSITION':accessor(delta,'VEC3')} for delta in morphs]
    if lower:
        normal_morphs=[np.zeros_like(normals) for _ in target_names]
        normal_morphs[3]=normals@rotation.T-normals;normal_morphs[7]=normal_morphs[3]*.55
        for target,delta in zip(targets,normal_morphs):target['NORMAL']=accessor(delta,'VEC3')
    mi=len(a.g['meshes']);a.g['meshes'].append({'name':name,'primitives':[{'attributes':attributes,'indices':accessor(tri.reshape(-1,1),'SCALAR',5123,34963),'material':material_index,'mode':4,'targets':targets}],'extras':{'targetNames':target_names},'weights':[0]*len(target_names)})
    node=copy.deepcopy(a.g['nodes'][face_node]);node.update(name=name,mesh=mi);node.pop('children',None);ni=len(a.g['nodes']);a.g['nodes'].append(node)
    parents=[node for node in a.g['nodes'][:-1] if face_node in node.get('children',[])]
    for parent in parents:parent['children'].append(ni)
    if not parents:
        for scene in a.g['scenes']:
            if face_node in scene['nodes']:scene['nodes'].append(ni)
    reports.append({'mesh':name,'vertices':n,'triangles':len(tri),'bounds_min':points.min(0).tolist(),'bounds_max':points.max(0).tolist(),'head_joint':head_joint})
def teeth(lower=False):
    bm=bmesh.new()
    for side in [-1,1]:
        for center,width,height in [(.0038,.0074,.0075),(.0105,.0056,.0068),(.0161,.0050,.0073),(.0215,.0054,.0065)]:
            x=side*center;z=.091-.022*(x/.028)**2
            if lower:width*=.95;height*=.82;z-=.0012
            offset=.001*(abs(x)/.025)**1.5
            y=(1.5202-offset-height/2) if lower else (1.52185-offset+height/2)
            part=bmesh.new();bmesh.ops.create_cube(part,size=1)
            for vertex in part.verts:vertex.co=Vector((vertex.co.x*width,vertex.co.y*height,vertex.co.z*.004))
            bmesh.ops.bevel(part,geom=list(part.edges),offset=.0007,segments=2,affect='EDGES',clamp_overlap=True)
            angle=math.atan(-2*.022*x/(.028**2));rotation=Matrix.Rotation(-angle,3,'Y')
            mapped={v:bm.verts.new(rotation@v.co+Vector((x,y,z))) for v in part.verts}
            for face in part.faces:bm.faces.new([mapped[v] for v in face.verts])
            part.free()
    finish('SM_Character_LowerTeeth' if lower else 'SM_Character_UpperTeeth',bm,enamel,lower,mouth_drop=.003)
teeth();teeth(True)
bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=24,v_segments=12,radius=1)
for vertex in bm.verts:
    p=vertex.co.copy();vertex.co=Vector((p.x*.0125,1.5178+p.y*.0030,.0725+p.z*.0115))
finish('SM_Character_Tongue',bm,tissue,True,mouth_drop=.0032)
a.bin.extend(b'\0'*((-len(a.bin))%4));a.g['buffers'][0]['byteLength']=len(a.bin)
a.save(root/'outputs/zachary_character_v33_candidate.glb')
(root/'work/oral33-changes.json').write_text(json.dumps({'new_meshes':reports,'anatomy_basis':'Artistic approximation; no open-mouth personal reference','source':'v32','source_face_geometry_and_morphs':'unchanged'},indent=2))
print(json.dumps(reports))
