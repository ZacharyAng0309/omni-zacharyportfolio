from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[1];work=root/'work';project=Path('D:/omni-workstation/projects/ZacharyPortfolio');vault=Path('D:/omni-workstation/vault/01_Wiki/Projects/ZacharyPortfolio')
record=json.loads((work/'avatar-latest-v38.json').read_text());current=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert current['latest_verified_review_version']=='v37','Re-read concurrent shared changes before proceeding'
archive=(project/record['archive']).resolve();assert archive.is_relative_to((project/'artifacts').resolve());note=vault/'07_Documentation/avatar_v38_hair_refinement_review.md';assert not archive.exists() and not note.exists()
assert json.loads((work/'hair38-validation.json').read_text())['checks_failed']==0
assert json.loads((work/'blend38-validation.json').read_text())['morph_meshes_synchronized']==6
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,data in record['files'].items():assert digest(root/'outputs'/name)==data['sha256']
assert digest(project/'public/models/zachary_character.glb')=='df73e3ad3c62e935962ef6cf82491ccb725a17c82ca0284711fd50b8d647ac08'
(archive/'outputs').mkdir(parents=True);(archive/'work').mkdir();manifest=[]
for name,data in record['files'].items():
 dest=archive/'outputs'/name;shutil.copy2(root/'outputs'/name,dest);assert digest(dest)==data['sha256'];manifest.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest(dest),'verified':True})
shutil.copy2(root/'outputs/zachary_character_v37_candidate.glb',archive/'outputs/zachary_character_v37_candidate.glb')
names=['glb_asset.py','review37.py','hair38-shape.py','hair38-shape.json','hair38-shape.glb','hair38-surface.py','hair38-reference-analysis.md','hair38-bake.py','hair38-bake.json','hair38-bake-final.log','hair38-embed.py','hair38-textures.json','verify38.py','hair38-validation.json','prepare38-review.py','review38.py','whole38.py','rig38-review.py','rig38-review.json','expression38-review.py','expression38-review.log','finalize38.py','reopen38.py','blend38-validation.json','build38.log','poses27.json','portrait37-front.png','deliver38.py','archive38.py']
for name in names:shutil.copy2(work/name,archive/'work'/name)
for pattern in ['hair38-*-raw.png','hair38-*.webp','hair38-parameters.png','portrait38-*.png','expression38-*.png']:
 for path in work.glob(pattern):
  if '-q' not in path.stem:shutil.copy2(path,archive/'work'/path.name)
shutil.copy2(project/'src/graphics/SceneController.ts',archive/'work/SceneController-at-review.ts')
(archive/'manifest.json').write_text(json.dumps(manifest,indent=2));(work/'archive38-validation.json').write_text(json.dumps(manifest,indent=2))
note.write_text('''---
id: DOC-ZacharyPortfolio-Avatar-v38-HairRefinement
title: Avatar crown part and hair strand refinement review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, hair, review]
created_at: 2026-11-15
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'''+(root/'outputs/Avatar-v38-Review.md').read_text(encoding='utf-8'),encoding='utf-8')
index=vault/'07_Documentation/index.md';content=index.read_text(encoding='utf-8')
if 'avatar_v38_hair_refinement_review' not in content:index.write_text(content+'\n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v38_hair_refinement_review|Avatar v38 Crown Part and Hair Strand Refinement Review]]\n',encoding='utf-8')
design=vault/'03_Design/persona_biometrics_and_likeness.md';content=design.read_text(encoding='utf-8')
if 'Crown part and strand refinement - 15 November 2026' not in content:
 content+='''

## Crown part and strand refinement - 15 November 2026

v38 introduces a soft crown-part dip (130 existing hair vertex copies; maximum 5.448 mm downward movement), with all mesh boundaries pinned. Three directional strand scales follow a comb field tilted toward the frontal part. Cycles bakes replace only the hair albedo, normal and packed roughness/specular maps, retaining the established UVs. All 135 matched face/hair seam pairs, rig weights, facial targets and unrelated material data remain unchanged. 337 preservation, geometry and budget checks passed, followed by fresh GLB renders and reopening of the final Blender review. The model remains NO-SHIP: jagged fringe transitions, loose silhouette strands, side/rear lumps, skin/eye fidelity and browser integration remain unfinished. Side/back grooming is inferred from one frontal photograph.

Evidence and integration contract: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v38_hair_refinement_review]].
'''
 design.write_text(content,encoding='utf-8')
for source,name in [('avatar-latest-v38.json','avatar-latest.json'),('AVATAR_LATEST-v38.md','AVATAR_LATEST.md')]:shutil.copy2(work/source,archive/name);shutil.copy2(work/source,project/name)
saved=json.loads((project/'avatar-latest.json').read_text())
for data in saved['files'].values():assert digest(project/data['path'])==data['sha256']
print('ARCHIVED',archive,'verified deliverables',len(manifest))
