from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];work=root/'work'
for name in ['review40.py','whole40.py','rig40-review.py','expression40-review.py','finalize40.py','reopen40.py']:
 text=(work/name).read_text(encoding='utf-8')
 for old,new in [('v40','v42'),('portrait40','portrait42'),('full40','full42'),('rig40','rig42'),('expression40','expression42'),('blend40','blend42')]:text=text.replace(old,new)
 if name=='review40.py':text=text.replace("if '--full' in arguments:\n    views", "if '--quick' in arguments:\n    views = views[:2]\nif '--full' in arguments:\n    views",1)
 (work/name.replace('40','42')).write_text(text,encoding='utf-8')
pose=json.loads((root/'outputs/avatar-v40-pose-targets.json').read_text());pose['avatarVersion']='v42';(root/'outputs/avatar-v42-pose-targets.json').write_text(json.dumps(pose,indent=2))
