"""Full-body, material-domain, and rig inventory for the whole-model review."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
scene = bpy.data.scenes['Portrait review v25']
bpy.context.window.scene = scene
scene.cycles.samples = 24
scene.render.resolution_x = 750
scene.render.resolution_y = 1000
camera = scene.camera
camera.data.ortho_scale = 1.95
target = Vector((0, 0, .88))
lights = [('LGT_Key', (-2, -3, 3), 500), ('LGT_Fill', (2, -1, 2), 250), ('LGT_Rim', (0, 2, 2.2), 350)]
for name, location, energy in lights:
    light = scene.objects[name]
    light.location = location
    light.data.energy = energy
    light.data.size = 2
    light.rotation_euler = (target - light.location).to_track_quat('-Z', 'Y').to_euler()
for label, location in [('front', (0, -4, .88)), ('quarter', (2, -3.5, .88)), ('back', (0, 4, .88))]:
    camera.location = location
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(root / f'work/full25-{label}.png')
    bpy.ops.render.render(write_still=True)
camera.data.ortho_scale = .32
scene.render.resolution_x = 640
scene.render.resolution_y = 640
target = Vector((-.355, -.04, .83))
camera.location = (-.355, -3, .83)
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = str(root / 'work/full25-hand.png')
bpy.ops.render.render(write_still=True)
rig = next(obj for obj in scene.objects if obj.type == 'ARMATURE')
report = {
    'units': scene.unit_settings.system,
    'objects': [{'name': obj.name, 'dimensions_m': list(obj.dimensions),
                 'location_m': list(obj.location), 'vertices': len(obj.data.vertices),
                 'triangles': sum(len(poly.vertices) - 2 for poly in obj.data.polygons),
                 'materials': [mat.name for mat in obj.data.materials]}
                for obj in scene.objects if obj.type == 'MESH'],
    'bones': [{'name': bone.name, 'head': list(bone.head_local), 'tail': list(bone.tail_local)}
              for bone in rig.data.bones],
}
(root / 'work/full25-audit.json').write_text(json.dumps(report, indent=2))
