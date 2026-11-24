from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[1];work=root/'work';project=Path('D:/omni-workstation/projects/ZacharyPortfolio');vault=Path('D:/omni-workstation/vault/01_Wiki/Projects/ZacharyPortfolio')
record=json.loads((work/'avatar-latest-v40.json').read_text());baseline=json.loads((work/'resume40-baseline.json').read_text(encoding='utf-8-sig'));current=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert current==baseline,'Reconcile concurrent handoff changes first'
archive=(project/record['archive']).resolve();assert archive.is_relative_to((project/'artifacts').resolve());note=vault/'07_Documentation/avatar_v40_fringe_repair_review.md';assert not archive.exists() and not note.exists()
assert json.loads((work/'fringe40-validation.json').read_text())['checks_failed']==0;assert json.loads((work/'blend40-validation.json').read_text())['morph_meshes_synchronized']==6
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,data in record['files'].items():assert digest(root/'outputs'/name)==data['sha256']
assert digest(project/baseline['application_model']['path'])==baseline['application_model']['sha256']
(archive/'outputs').mkdir(parents=True);(archive/'work').mkdir();manifest=[]
for name,data in record['files'].items():
 dest=archive/'outputs'/name;shutil.copy2(root/'outputs'/name,dest);assert digest(dest)==data['sha256'];manifest.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest(dest),'verified':True})
shutil.copy2(root/'outputs/zachary_character_v39_candidate.glb',archive/'outputs/zachary_character_v39_candidate.glb')
names=['glb_asset.py','review39.py','fringe40-shape.py','fringe40-shape.glb','fringe40-shape.json','fringe40-paint.py','fringe40-paint.blend','fringe40-paint.log','fringe40-guides.json','fringe40-patch-bake.py','fringe40-patch-bake.json','fringe40-patch-bake.log','fringe40-patch-uv.npz','fringe40-patch-embed.py','fringe40-vertex-mapping.json','fringe40-face-raw.png','fringe40-hair-raw.png','fringe40-face.webp','fringe40-hair.webp','fringe40-textures.json','fringe40-render-comparison.json','verify40.py','fringe40-validation.json','prepare40-review.py','review40.py','whole40.py','rig40-review.py','rig40-review.json','expression40-review.py','expression40-review.log','finalize40.py','reopen40.py','blend40-validation.json','reopen40.log','build40.log','poses27.json','portrait39-front.png','resume40-baseline.json','qa40-contact.jpg','deliver40.py','archive40.py']
for name in names:shutil.copy2(work/name,archive/'work'/name)
for pattern in ['portrait40-*.png','expression40-*.png','fringe40-preview-*.png']:
 for path in work.glob(pattern):shutil.copy2(path,archive/'work'/path.name)
shutil.copy2(project/'src/graphics/SceneController.ts',archive/'work/SceneController-at-archive.ts')
(archive/'manifest.json').write_text(json.dumps(manifest,indent=2));(work/'archive40-validation.json').write_text(json.dumps(manifest,indent=2))
note.write_text('''---
id: DOC-ZacharyPortfolio-Avatar-v40-FringeRepair
title: Avatar painted fringe texture repair review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, hair, texture, review]
created_at: 2026-11-19
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'''+(root/'outputs/Avatar-v40-Review.md').read_text(encoding='utf-8'),encoding='utf-8')
index=vault/'07_Documentation/index.md';content=index.read_text(encoding='utf-8')
if 'avatar_v40_fringe_repair_review' not in content:index.write_text(content+'\n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v40_fringe_repair_review|Avatar v40 Painted Fringe Texture Repair Review]]\n',encoding='utf-8')
design=vault/'03_Design/persona_biometrics_and_likeness.md';content=design.read_text(encoding='utf-8')
if 'Painted fringe texture repair - 17 November 2026' not in content:
 content+='''

## Painted fringe texture repair - 17 November 2026

v40 harmonizes the mismatched fringe colors across Face/Hair and gives the local repair dedicated texture space. The patch uses angle-based UV islands in unused 768×768 atlas rectangles, without increasing texture dimensions or image count. Base color now uses TEXCOORD_2; preserve original UV0/UV1 for other maps. 552 UV vertex copies retain source geometry, weights and all morph deltas. Local surface relaxation below the part moves 14 Face and 38 Hair source vertex copies by at most 2.001 mm, protecting active facial vertices and keeping all 135 shared seam pairs coincident. 1,196 preservation/mapping/geometry/color/budget checks passed, including zero sampled UV overlaps. Fresh GLB renders match the authored Blender fringe preview, and the final review file was reopened. Hair remains stylized; v38 remains integrated in the portfolio until v40 browser checks are completed.

Evidence and authoring workflow: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v40_fringe_repair_review]].
'''
 design.write_text(content,encoding='utf-8')
for source,name in [('AVATAR_LATEST-v40.md','AVATAR_LATEST.md'),('avatar-latest-v40.json','avatar-latest.json')]:shutil.copy2(work/source,archive/name);shutil.copy2(work/source,project/name)
saved=json.loads((project/'avatar-latest.json').read_text())
for data in saved['files'].values():assert digest(project/data['path'])==data['sha256']
assert saved['application_model']['integrated_version']=='v38';assert digest(project/saved['application_model']['path'])==baseline['application_model']['sha256']
print('ARCHIVED',archive,'verified deliverables',len(manifest),'public v38 model preserved')
