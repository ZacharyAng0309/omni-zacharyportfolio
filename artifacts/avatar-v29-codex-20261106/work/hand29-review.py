"""Render exported finger-rig candidates and independently check their skinning."""
import bpy, sys, json, re
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root/'work'))
from glb_asset import Asset
from kinematics27 import world, rotation_xyz
conversion=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
def convert(point): return Vector((point[0],-point[2],point[1]))
reports={}
versions=[int(x) for x in sys.argv[sys.argv.index('--')+1:]] if '--' in sys.argv else [27,28]
for version in versions:
    asset=Asset(root/f'outputs/zachary_character_v{version}_candidate.glb')
    scene=bpy.data.scenes.new(f'Hand articulation review v{version}'); bpy.context.window.scene=scene
    scene.use_fake_user=True; scene.unit_settings.system='METRIC'
    bpy.ops.import_scene.gltf(filepath=str(asset.path))
    for obj in scene.objects:
        if obj.type=='MESH': obj.hide_render=not (obj.name.startswith('SM_Character_Hands') or obj.name.startswith('SM_Cloth_Hoodie'))
    rig=next(obj for obj in scene.objects if obj.type=='ARMATURE')
    scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
    scene.render.resolution_x=700; scene.render.resolution_y=700; scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Hand review world'); scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    target=convert((-.389,.827,.068))
    camera=bpy.data.objects.new('CAM_Hand',bpy.data.cameras.new('CAM_Hand')); scene.collection.objects.link(camera); scene.camera=camera
    camera.data.type='ORTHO'; camera.data.ortho_scale=.21
    for name,offset,energy in [('Key',(-1,-1,1),55),('Fill',(1,0,.5),35)]:
        data=bpy.data.lights.new('LGT_'+name,'AREA'); data.energy=energy; data.size=1.2
        obj=bpy.data.objects.new(data.name,data); scene.collection.objects.link(obj); obj.location=target+Vector(offset)
        obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    rest=world(node_data=asset.g['nodes'])
    joints=asset.g['skins'][0]['joints']; names=[asset.g['nodes'][i]['name'] for i in joints]
    bind=asset.arr(asset.g['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    prim=asset.prim('SM_Character_Hands'); points=asset.pos('SM_Character_Hands')
    homogeneous=np.column_stack([points,np.ones(len(points))])
    indices=asset.arr(prim['attributes']['JOINTS_0']).astype(int); weights=asset.arr(prim['attributes']['WEIGHTS_0'])
    triangles=asset.arr(prim['indices']).reshape(-1,3)
    edges=np.unique(np.sort(np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]),axis=1),axis=0)
    lengths=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)
    obj=next(obj for obj in scene.objects if obj.name.startswith('SM_Character_Hands'))
    lookup={tuple(round(value,5) for value in vertex.co):vertex.index for vertex in obj.data.vertices}
    report={}
    for pose_index,curl in enumerate([0,.15,.35,.6]):
        frame=1+pose_index*40; scene.frame_set(frame)
        local_nodes=json.loads(json.dumps(asset.g['nodes']))
        from kinematics27 import rotation_quaternion
        def qm(a,b):
            ax,ay,az,aw=a; bx,by,bz,bw=b
            return [aw*bx+ax*bw+ay*bz-az*by,aw*by-ax*bz+ay*bw+az*bx,aw*bz+ax*by-ay*bx+az*bw,aw*bw-ax*bx-ay*by-az*bz]
        for node in local_nodes:
            if re.fullmatch('(Left|Right)Hand(Thumb|Index|Middle|Ring|Pinky)[123]',node.get('name','')):
                angle=curl*(.55 if 'Thumb' in node['name'] else 1)
                node['rotation']=qm(node.get('rotation',[0,0,0,1]),[float(np.sin(angle/2)),0,0,float(np.cos(angle/2))])
        posed=world(node_data=local_nodes)
        desired={}
        for bone in rig.data.bones:
            delta=conversion@Matrix((posed[bone.name]@np.linalg.inv(rest[bone.name])).tolist())@conversion.inverted()
            desired[bone.name]=rig.matrix_world.inverted()@delta@rig.matrix_world@bone.matrix_local
        for bone in rig.data.bones:
            basis=bone.matrix_local.inverted()@desired[bone.name]
            if bone.parent: basis=bone.matrix_local.inverted()@bone.parent.matrix_local@desired[bone.parent.name].inverted()@desired[bone.name]
            pb=rig.pose.bones[bone.name]; pb.rotation_mode='QUATERNION'; pb.matrix_basis=basis
            for prop in ['location','rotation_quaternion','scale']: pb.keyframe_insert(data_path=prop,frame=frame,group=bone.name)
        bpy.context.view_layer.update()
        matrices=np.array([posed[name]@bind[i] for i,name in enumerate(names)])
        expected=np.einsum('nvij,nj,nv->ni',matrices[indices],homogeneous,weights)[:,:3]
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=evaluated.to_mesh(); errors=[]
        for i,point in enumerate(points):
            key=tuple(round(value,5) for value in convert(point))
            if key in lookup: errors.append((evaluated.matrix_world@mesh.vertices[lookup[key]].co-convert(expected[i])).length*1000)
        evaluated.to_mesh_clear()
        assert max(errors)<.01
        ratios=np.linalg.norm(expected[edges[:,0]]-expected[edges[:,1]],axis=1)/np.maximum(lengths,1e-8)
        report[str(curl)]={'sampled_vertices':len(errors),'max_skinning_error_mm':max(errors),'edge_stretch_p99':float(np.percentile(ratios,99)),'edge_stretch_max':float(ratios.max())}
        scene.timeline_markers.new(f'Curl {curl}',frame=frame)
        for label,offset in [('outer',(-1,0,0)),('front',(0,0,1))]:
            camera.location=target+convert(offset); camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
            scene.render.filepath=str(root/f'work/hand-v{version}-{curl:.2f}-{label}.png'); bpy.ops.render.render(write_still=True)
        if curl in [0,.35]:
            left_target=convert((.386,.827,.068))
            for label,offset in [('outer',(1,0,0)),('front',(0,0,1))]:
                camera.location=left_target+convert(offset);camera.rotation_euler=(left_target-camera.location).to_track_quat('-Z','Y').to_euler()
                scene.render.filepath=str(root/f'work/hand-v{version}-left-{curl:.2f}-{label}.png');bpy.ops.render.render(write_still=True)
    scene.frame_start=1;scene.frame_end=121;scene.frame_set(1)
    reports[str(version)]=report
    if version==29:
        camera.location=target+convert((-1,0,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        bpy.ops.wm.save_as_mainfile(filepath=str(root/'outputs/Zachary_Avatar_v29_Review.blend'),compress=True)
(root/'work/hand29-review.json').write_text(json.dumps(reports,indent=2)); print(json.dumps(reports))
