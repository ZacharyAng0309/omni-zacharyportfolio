from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[1];work=root/'work';project=Path('D:/omni-workstation/projects/ZacharyPortfolio');vault=Path('D:/omni-workstation/vault/01_Wiki/Projects/ZacharyPortfolio')
record=json.loads((work/'avatar-latest-v36.json').read_text());current=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert current['latest_verified_review_version']=='v35','Re-read concurrent shared changes before proceeding'
archive=(project/record['archive']).resolve();assert archive.is_relative_to((project/'artifacts').resolve());note=vault/'07_Documentation/avatar_v36_eyelids_review.md';assert not archive.exists() and not note.exists()
validation=json.loads((work/'eye36-validation.json').read_text());bv=json.loads((work/'blend36-validation.json').read_text());assert validation['checks_failed']==0 and bv['morph_meshes_synchronized']==6
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,data in record['files'].items():assert digest(root/'outputs'/name)==data['sha256']
assert digest(project/'public/models/zachary_character.glb')=='df73e3ad3c62e935962ef6cf82491ccb725a17c82ca0284711fd50b8d647ac08'
(archive/'outputs').mkdir(parents=True);(archive/'work').mkdir();manifest=[]
for name,data in record['files'].items():
 dest=archive/'outputs'/name;shutil.copy2(root/'outputs'/name,dest);assert digest(dest)==data['sha256'];manifest.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest(dest),'verified':True})
shutil.copy2(root/'outputs/zachary_character_v35_candidate.glb',archive/'outputs/zachary_character_v35_candidate.glb')
names=['glb_asset.py','eye36-probe.py','eye36-probe.json','eye36-patch-1.npz','eye36-patch1.npz','eye36-build.py','eye36-build.log','eye36-generated.npz','eye36-globe-1.npz','eye36-globe1.npz','eye36-rings.json','eye36-lids.png','eye36-export.py','verify36.py','eye36-validation.json','eye36-validation.log','review36.py','whole36.py','rig36-review.py','rig36-review.json','expression36-review.py','expression36-review.log','finalize36.py','reopen36.py','blend36-validation.json','build36.log','poses27.json','expression35-neutral.png','deliver36.py','archive36.py']
for name in names:shutil.copy2(work/name,archive/'work'/name)
shutil.copy2(work/'zachary_character_v36_eye_prototype.glb',archive/'work/zachary_character_v36_eye_prototype.glb')
for pattern in ['expression36-*.png','portrait36-*.png']:
 for p in work.glob(pattern):shutil.copy2(p,archive/'work'/p.name)
shutil.copy2(project/'src/graphics/SceneController.ts',archive/'work/SceneController-at-review.ts')
(archive/'manifest.json').write_text(json.dumps(manifest,indent=2));(work/'archive36-validation.json').write_text(json.dumps(manifest,indent=2))
note.write_text('''---
id: DOC-ZacharyPortfolio-Avatar-v36-Eyelids
title: Avatar separate eye and eyelid review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, rig, face, review]
created_at: 2026-11-14
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'''+(root/'outputs/Avatar-v36-Review.md').read_text(encoding='utf-8'),encoding='utf-8')
index=vault/'07_Documentation/index.md';content=index.read_text(encoding='utf-8')
if 'avatar_v36_eyelids_review' not in content:index.write_text(content+'\n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v36_eyelids_review|Avatar v36 Separate Eyes and Eyelids Review]]\n',encoding='utf-8')
design=vault/'03_Design/persona_biometrics_and_likeness.md';content=design.read_text(encoding='utf-8')
if 'Separate eyes and eyelids - 14 November 2026' not in content:
 content+='''

## Separate eyes and eyelids - 14 November 2026

v36 replaces painted surface eyes with two true openings, a fitted eyelid mesh and separate closed globes. It introduces depth motion for the outer blink and four nested lid loops per eye, with exact contact and retained rim thickness at closure. A source-skin Cycles bake supplies the lid texture. Numeric checks cover 10 eye cases, seam correspondence, front orientation, nonzero areas, closed-globe topology and sampled eye visibility; final Blender expressions and the saved review file were inspected. The eye appearance is still an artistic approximation and needs iris/cornea and upper-lid likeness refinement. This remains a review candidate.

IMPORTANT: schema version 4 adds SM_Character_Eyelids to the facial synchronization contract. Animate all six named facial meshes; the two globes follow Head without gaze controls. The public model remains unchanged.

Evidence and scope: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v36_eyelids_review]].
'''
 design.write_text(content,encoding='utf-8')
for source,name in [('avatar-latest-v36.json','avatar-latest.json'),('AVATAR_LATEST-v36.md','AVATAR_LATEST.md')]:shutil.copy2(work/source,archive/name);shutil.copy2(work/source,project/name)
saved=json.loads((project/'avatar-latest.json').read_text())
for data in saved['files'].values():assert digest(project/data['path'])==data['sha256']
print('ARCHIVED',archive,'verified deliverables',len(manifest))
