import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
asset=Asset(root/'outputs/zachary_character_v38_candidate.glb')
scene=bpy.data.scenes['Whole model review v38'];bpy.context.window.scene=scene
rig=next(obj for obj in scene.objects if obj.type=='ARMATURE');errors={}
for frame,targets in {41:{'RightHand':(-.18,1.51,.13)},81:{'RightHand':(-.21,1.12,.24),'LeftHand':(.21,1.12,.24)},121:{'RightHand':(-.37,1.20,.24)}}.items():
    scene.frame_set(frame);bpy.context.view_layer.update();row={}
    for name,(x,y,z) in targets.items():
        error=(rig.matrix_world@rig.pose.bones[name].head-Vector((x,-z,y))).length*1000
        assert error<.1;row[name]=error
    errors[str(frame)]=row
facial=bpy.data.scenes['Facial expression review v38'];bpy.context.window.scene=facial
objects=[o for o in facial.objects if o.type=='MESH' and o.data.shape_keys]
assert len(objects)==6
expected={1:{},41:{'eyeBlinkLeft':1,'eyeBlinkRight':1},81:{'mouthSmileLeft':.42,'mouthSmileRight':.42},121:{'jawOpen':.45},161:{'viseme_aa':.65,'mouthOpen':.35},201:{'mouthSmileLeft':.42,'mouthSmileRight':.42,'viseme_aa':.65,'mouthOpen':.35},241:{'mouthOpen':1},281:{'jawOpen':1,'mouthOpen':1},321:{'viseme_aa':1},361:{'mouthSmileLeft':.6,'mouthOpen':.4},401:{'eyeBlinkLeft':.5,'eyeBlinkRight':.5},441:{'eyeBlinkLeft':1},481:{'eyeBlinkRight':1},521:{'eyeBlinkLeft':1,'eyeBlinkRight':1,'browInnerUp':1}}
for frame,values in expected.items():
    facial.frame_set(frame);bpy.context.view_layer.update()
    for obj in objects:
        for key in obj.data.shape_keys.key_blocks:
            if key.name!='Basis':assert abs(key.value-values.get(key.name,0))<1e-6,(frame,obj.name,key.name)
conversion=np.array([[1,0,0],[0,0,-1],[0,1,0]])
shape_errors={}
for obj in objects:
    name=next(m['name'] for m in asset.g['meshes'] if obj.name.startswith(m['name']) and 'targets' in m['primitives'][0])
    mesh=next(m for m in asset.g['meshes'] if m['name']==name);primitive=mesh['primitives'][0]
    points=asset.arr(primitive['attributes']['POSITION'])@conversion.T
    target_arrays=[asset.arr(t['POSITION'])@conversion.T for t in primitive['targets']]
    names=mesh['extras']['targetNames'];tree=KDTree(len(points))
    for i,point in enumerate(points):tree.insert(point,i)
    tree.balance();maximum=0
    for vertex in obj.data.vertices:
        basis=obj.data.shape_keys.key_blocks['Basis'].data[vertex.index].co
        candidates=tree.find_range(basis,2e-6);assert candidates,(obj.name,vertex.index)
        values=np.array([obj.data.shape_keys.key_blocks[name].data[vertex.index].co-basis for name in names])
        error=min(float(np.linalg.norm(values-np.array([a[i] for a in target_arrays]),axis=1).max()) for _,i,_ in candidates)
        maximum=max(maximum,error)
    assert maximum<2e-6
    shape_errors[name]={'checked_vertices':len(obj.data.vertices),'maximum_morph_error_mm':maximum*1000}
images=set()
for review_scene in [scene,facial]:
    for obj in review_scene.objects:
        if obj.type!='MESH':continue
        for mat in obj.data.materials:
            images.update(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
assert all(image.packed_file for image in images)
report={'reopened_gesture_errors_mm':errors,'facial_frames_verified':list(expected),'morph_meshes_synchronized':len(objects),'all_imported_morph_vertices':shape_errors,'packed_image_datablocks':len(images),'retained_review_scenes':[scene.name,facial.name]}
(root/'work/blend38-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
