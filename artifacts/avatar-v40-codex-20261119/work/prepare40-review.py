from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];work=root/'work'
for name in ['review39.py','whole39.py','rig39-review.py','expression39-review.py','finalize39.py','reopen39.py']:
 text=(work/name).read_text(encoding='utf-8')
 for old,new in [('v39','v40'),('portrait39','portrait40'),('full39','full40'),('rig39','rig40'),('expression39','expression40'),('blend39','blend40')]:text=text.replace(old,new)
 (work/name.replace('39','40')).write_text(text,encoding='utf-8')
pose=json.loads((root/'outputs/avatar-v39-pose-targets.json').read_text());pose['avatarVersion']='v40';(root/'outputs/avatar-v40-pose-targets.json').write_text(json.dumps(pose,indent=2))
