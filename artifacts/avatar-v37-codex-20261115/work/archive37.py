from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[1];work=root/'work';project=Path('D:/omni-workstation/projects/ZacharyPortfolio');vault=Path('D:/omni-workstation/vault/01_Wiki/Projects/ZacharyPortfolio')
record=json.loads((work/'avatar-latest-v37.json').read_text());current=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert current['latest_verified_review_version']=='v36','Re-read concurrent shared changes before proceeding'
archive=(project/record['archive']).resolve();assert archive.is_relative_to((project/'artifacts').resolve());note=vault/'07_Documentation/avatar_v37_eye_tuning_review.md';assert not archive.exists() and not note.exists()
validation=json.loads((work/'eye37-validation.json').read_text());bv=json.loads((work/'blend37-validation.json').read_text());assert validation['checks_failed']==0 and bv['morph_meshes_synchronized']==6
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,data in record['files'].items():assert digest(root/'outputs'/name)==data['sha256']
assert digest(project/'public/models/zachary_character.glb')=='df73e3ad3c62e935962ef6cf82491ccb725a17c82ca0284711fd50b8d647ac08'
(archive/'outputs').mkdir(parents=True);(archive/'work').mkdir();manifest=[]
for name,data in record['files'].items():
 dest=archive/'outputs'/name;shutil.copy2(root/'outputs'/name,dest);assert digest(dest)==data['sha256'];manifest.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest(dest),'verified':True})
shutil.copy2(root/'outputs/zachary_character_v36_candidate.glb',archive/'outputs/zachary_character_v36_candidate.glb')
names=['glb_asset.py','tune37.py','tune37.log','tune37-changes.json','verify37.py','eye37-validation.json','eye37-validation.log','eye36-rings.json','review37.py','whole37.py','rig37-review.py','rig37-review.json','expression37-review.py','expression37-review.log','finalize37.py','reopen37.py','blend37-validation.json','build37.log','poses27.json','expression36-neutral.png','deliver37.py','archive37.py']
for name in names:shutil.copy2(work/name,archive/'work'/name)
shutil.copy2(work/'zachary_character_v37_tuning.glb',archive/'work/zachary_character_v37_tuning.glb')
for pattern in ['expression37-*.png','portrait37-*.png']:
 for p in work.glob(pattern):shutil.copy2(p,archive/'work'/p.name)
shutil.copy2(project/'src/graphics/SceneController.ts',archive/'work/SceneController-at-review.ts')
(archive/'manifest.json').write_text(json.dumps(manifest,indent=2));(work/'archive37-validation.json').write_text(json.dumps(manifest,indent=2))
note.write_text('''---
id: DOC-ZacharyPortfolio-Avatar-v37-EyeTuning
title: Avatar eye placement and iris tuning review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, rig, face, review]
created_at: 2026-11-15
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'''+(root/'outputs/Avatar-v37-Review.md').read_text(encoding='utf-8'),encoding='utf-8')
index=vault/'07_Documentation/index.md';content=index.read_text(encoding='utf-8')
if 'avatar_v37_eye_tuning_review' not in content:index.write_text(content+'\n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v37_eye_tuning_review|Avatar v37 Eye Placement and Iris Tuning Review]]\n',encoding='utf-8')
design=vault/'03_Design/persona_biometrics_and_likeness.md';content=design.read_text(encoding='utf-8')
if 'Eye placement and iris tuning - 15 November 2026' not in content:
 content+='''

## Eye placement and iris tuning - 15 November 2026

v37 lowers the eye assembly by 1.6 mm with local face/fringe support, reduces pupil radius to 2.0 mm, enlarges iris radius to 5.8 mm, and adds an angled/full opening plus a restrained 0.2 mm upper-lid crease. These are artistic adjustments from the frontal reference, not calibrated biometric measurements. The closed endpoint is preserved before eye translation. Topology, UVs, seven image payloads, weights and original Face targets remain unchanged. All 135 shared skin/hair seam pairs remain coincident. Numeric preservation, orientation, deformation and sampled visibility checks passed; the final Blender file was reopened with six synchronized facial meshes. Eye shading, subtle asymmetry and skin fidelity remain unfinished.

Evidence and integration contract: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v37_eye_tuning_review]].
'''
 design.write_text(content,encoding='utf-8')
for source,name in [('avatar-latest-v37.json','avatar-latest.json'),('AVATAR_LATEST-v37.md','AVATAR_LATEST.md')]:shutil.copy2(work/source,archive/name);shutil.copy2(work/source,project/name)
saved=json.loads((project/'avatar-latest.json').read_text())
for data in saved['files'].values():assert digest(project/data['path'])==data['sha256']
print('ARCHIVED',archive,'verified deliverables',len(manifest))
