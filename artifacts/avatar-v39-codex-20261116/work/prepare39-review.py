from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];work=root/'work'
for name in ['review38.py','whole38.py','rig38-review.py','expression38-review.py','finalize38.py','reopen38.py']:
 text=(work/name).read_text(encoding='utf-8')
 for old,new in [('v38','v39'),('portrait38','portrait39'),('full38','full39'),('rig38','rig39'),('expression38','expression39'),('blend38','blend39')]:text=text.replace(old,new)
 (work/name.replace('38','39')).write_text(text,encoding='utf-8')
pose=json.loads((root/'outputs/avatar-v38-pose-targets.json').read_text());pose['avatarVersion']='v39';(root/'outputs/avatar-v39-pose-targets.json').write_text(json.dumps(pose,indent=2))
