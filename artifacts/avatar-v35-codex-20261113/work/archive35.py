from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[1];work=root/'work';project=Path('D:/omni-workstation/projects/ZacharyPortfolio');vault=Path('D:/omni-workstation/vault/01_Wiki/Projects/ZacharyPortfolio')
record=json.loads((work/'avatar-latest-v35.json').read_text());current=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert current['latest_verified_review_version']=='v34','Re-read concurrent shared changes before proceeding'
archive=(project/record['archive']).resolve();assert archive.is_relative_to((project/'artifacts').resolve());note=vault/'07_Documentation/avatar_v35_brow_fringe_review.md';assert not archive.exists() and not note.exists()
validation=json.loads((work/'verify35.json').read_text());bv=json.loads((work/'blend35-validation.json').read_text());assert validation['checks_failed']==0 and bv['morph_meshes_synchronized']==5
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,data in record['files'].items():assert digest(root/'outputs'/name)==data['sha256']
assert digest(project/'public/models/zachary_character.glb')=='df73e3ad3c62e935962ef6cf82491ccb725a17c82ca0284711fd50b8d647ac08'
(archive/'outputs').mkdir(parents=True);(archive/'work').mkdir();manifest=[]
for name,data in record['files'].items():
 dest=archive/'outputs'/name;shutil.copy2(root/'outputs'/name,dest);assert digest(dest)==data['sha256'];manifest.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest(dest),'verified':True})
shutil.copy2(root/'outputs/zachary_character_v34_candidate.glb',archive/'outputs/zachary_character_v34_candidate.glb')
names=['glb_asset.py','refine35.py','refine35-changes.json','verify35.py','verify35.json','review35.py','whole35.py','rig35-review.py','rig35-review.json','expression35-review.py','expression35-review.log','finalize35.py','reopen35.py','blend35-validation.json','build35.log','probe35.log','inspect35.py','inspect35-after.py','poses27.json','eye34-baked-data.npz','expression34-neutral.png','deliver35.py','archive35.py']
for name in names:shutil.copy2(work/name,archive/'work'/name)
for pattern in ['expression35-*.png','clay35-*.png','portrait35-*.png']:
 for p in work.glob(pattern):shutil.copy2(p,archive/'work'/p.name)
shutil.copy2(project/'src/graphics/SceneController.ts',archive/'work/SceneController-at-review.ts')
(archive/'manifest.json').write_text(json.dumps(manifest,indent=2));(work/'archive35-validation.json').write_text(json.dumps(manifest,indent=2))
note.write_text('''---
id: DOC-ZacharyPortfolio-Avatar-v35-BrowFringe
title: Avatar brow and fringe surface review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, rig, face, review]
created_at: 2026-11-13
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'''+(root/'outputs/Avatar-v35-Review.md').read_text(encoding='utf-8'),encoding='utf-8')
index=vault/'07_Documentation/index.md';content=index.read_text(encoding='utf-8')
if 'avatar_v35_brow_fringe_review' not in content:index.write_text(content+'\n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v35_brow_fringe_review|Avatar v35 Brow and Fringe Review]]\n',encoding='utf-8')
design=vault/'03_Design/persona_biometrics_and_likeness.md';content=design.read_text(encoding='utf-8')
if 'Brow and fringe review - 13 November 2026' not in content:
 content+='''

## Brow and fringe review - 13 November 2026

v35 is a subtle sub-millimeter surface cleanup across the upper face and fringe. It preserves all 135 original shared seam pairs, bounds, blink-active rest vertices, topology, UVs, textures, weights and target deltas. 319 checks and a fresh Blender reopen passed. The visible improvement is modest; anatomical eyelid loops and eye reconstruction are the next priority, because repeated local smoothing has diminishing benefit. This remains a review candidate.

Evidence and scope: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v35_brow_fringe_review]].
'''
 design.write_text(content,encoding='utf-8')
for source,name in [('avatar-latest-v35.json','avatar-latest.json'),('AVATAR_LATEST-v35.md','AVATAR_LATEST.md')]:shutil.copy2(work/source,archive/name);shutil.copy2(work/source,project/name)
saved=json.loads((project/'avatar-latest.json').read_text())
for data in saved['files'].values():assert digest(project/data['path'])==data['sha256']
print('ARCHIVED',archive,'verified deliverables',len(manifest))
