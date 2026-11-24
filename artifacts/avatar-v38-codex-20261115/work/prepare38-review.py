from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];work=root/'work'
for base in ['review','whole','rig','expression','finalize','reopen']:
 old={'rig':'rig37-review.py','expression':'expression37-review.py'}.get(base,base+'37.py')
 text=(work/old).read_text(encoding='utf-8')
 for a,b in [('v37','v38'),('portrait37','portrait38'),('full37','full38'),('rig37','rig38'),('expression37','expression38'),('blend37','blend38')]:text=text.replace(a,b)
 if base=='review':
  text=text.replace("views = [('front', (0, -3, 1.585)), ('quarter', (1.45, -2.62, 1.585))]","views = [('front', (0, -3, 1.585)), ('quarter', (1.45, -2.62, 1.585)), ('left', (-2.9, -.5, 1.585)), ('top', (.1, -2, 3)), ('back', (0, 3, 1.65))]")
 if base=='expression':
  text=text.replace('    bpy.ops.render.render(write_still=True)',"    if label in ['neutral','blink-brow','speech']:bpy.ops.render.render(write_still=True)")
 name=old.replace('37','38');(work/name).write_text(text,encoding='utf-8')
pose=json.loads((root/'outputs/avatar-v37-pose-targets.json').read_text());pose['avatarVersion']='v38';(root/'outputs/avatar-v38-pose-targets.json').write_text(json.dumps(pose,indent=2))
