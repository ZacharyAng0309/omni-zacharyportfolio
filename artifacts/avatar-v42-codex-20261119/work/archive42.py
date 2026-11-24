from pathlib import Path
import json,hashlib,shutil,sys
root=Path(__file__).resolve().parents[1];work=root/'work';project=Path('D:/omni-workstation/projects/ZacharyPortfolio');vault=Path('D:/omni-workstation/vault/01_Wiki/Projects/ZacharyPortfolio')
record=json.loads((work/'avatar-latest-v42.json').read_text());baseline=json.loads((work/'resume42-baseline.json').read_text(encoding='utf-8-sig'));current=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'))
assert current==baseline,'Reconcile concurrent handoff changes first'
archive=(project/record['archive']).resolve();assert archive.is_relative_to((project/'artifacts').resolve());note=vault/'07_Documentation/avatar_v42_hair_filaments_review.md'
assert not archive.exists() and not note.exists(),'Immutable archive/note already exists'
assert json.loads((work/'hair42-validation.json').read_text())['checks_failed']==0
assert json.loads((work/'blend42-validation.json').read_text())['morph_meshes_synchronized']==6
assert json.loads((work/'hair42-blender-validation.json').read_text())['conservative_minimum_forehead_clearance_mm']>0
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for name,data in record['files'].items():assert digest(root/'outputs'/name)==data['sha256']
assert digest(project/baseline['application_model']['path'])==baseline['application_model']['sha256']
names=['glb_asset.py','hair42-reference-analysis.md','hair42-build.py','hair42-build.json','hair42-build.log','hair42-shape.glb','hair42-filaments.npz','hair42-embed.py','fringe40-guides.json','verify42.py','hair42-validation.json','prepare42-review.py','review42.py','whole42.py','rig42-review.py','rig42-review.json','expression42-review.py','expression42-review.log','finalize42.py','finalize42.log','reopen42.py','reopen42.log','hair42-blender-check.py','hair42-blender-validation.json','blend42-validation.json','build42.log','poses27.json','resume42-baseline.json','deliver42.py','archive42.py']
for name in names:assert (work/name).is_file(),name
assert (root/'outputs/zachary_character_v41_candidate.glb').is_file()
if '--check' in sys.argv:print('ARCHIVE_PREFLIGHT_OK',record['archive']);sys.exit(0)
(archive/'outputs').mkdir(parents=True);(archive/'work').mkdir();manifest=[]
for name,data in record['files'].items():
 dest=archive/'outputs'/name;shutil.copy2(root/'outputs'/name,dest);assert digest(dest)==data['sha256'];manifest.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest(dest),'verified':True})
shutil.copy2(root/'outputs/zachary_character_v41_candidate.glb',archive/'outputs/zachary_character_v41_candidate.glb')
for name in names:shutil.copy2(work/name,archive/'work'/name)
for pattern in ['portrait42-*.png','expression42-*.png','hair42-baseline-*.png']:
 for path in work.glob(pattern):shutil.copy2(path,archive/'work'/path.name)
shutil.copy2(project/'src/graphics/SceneController.ts',archive/'work/SceneController-at-archive.ts')
(archive/'manifest.json').write_text(json.dumps(manifest,indent=2));(work/'archive42-validation.json').write_text(json.dumps(manifest,indent=2))
note.write_text('''---
id: DOC-ZacharyPortfolio-Avatar-v42-HairFilaments
title: Avatar crown and fine-strand refinement review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, hair, geometry, review]
created_at: 2026-11-19
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'''+(root/'outputs/Avatar-v42-Review.md').read_text(encoding='utf-8'),encoding='utf-8')
index=vault/'07_Documentation/index.md';content=index.read_text(encoding='utf-8')
if 'avatar_v42_hair_filaments_review' not in content:index.write_text(content+'\n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v42_hair_filaments_review|Avatar v42 Crown and Fine-Strand Refinement Review]]\n',encoding='utf-8')
design=vault/'03_Design/persona_biometrics_and_likeness.md';content=design.read_text(encoding='utf-8')
if 'Crown and fine-strand refinement - 19 November 2026' not in content:
 content+='''

## Crown and fine-strand refinement - 19 November 2026

v42 builds on integrated v41, preserving its face/eye/ear/eyelid/glasses geometry, original UVs, all seven image payloads, rig and facial targets. Bounded Laplacian crown relaxation moves 653 hair vertex copies by at most 1.801 mm, retaining every Face/Hair seam and lower fringe. Thirty-eight sparse round tapered filaments soften the fringe/crown edges. Their 1,256 vertices use nearest-surface weight transfer and follow Head exactly; opaque vertex colors add no texture image. This adds 2,360 triangles and one material/draw call. The final asset totals 47,270 triangles and 2,678,460 bytes. All 449 preservation/geometry/rig/budget checks passed; fresh Blender renders and the saved-file reopen verify fourteen facial frames, gestures, head turns and sampled raised-brow clearance. Hair remains stylized. v41 remains integrated until the new filament material is checked under application lighting, anti-aliasing and camera distances.

Evidence and authoring workflow: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v42_hair_filaments_review]].
'''
 design.write_text(content,encoding='utf-8')
# Fail before publishing the new authoritative pointer if another agent changed it.
assert json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'))==baseline
assert digest(project/baseline['application_model']['path'])==baseline['application_model']['sha256']
for source,name in [('AVATAR_LATEST-v42.md','AVATAR_LATEST.md'),('avatar-latest-v42.json','avatar-latest.json')]:
 shutil.copy2(work/source,archive/name);shutil.copy2(work/source,project/name)
saved=json.loads((project/'avatar-latest.json').read_text())
for data in saved['files'].values():assert digest(project/data['path'])==data['sha256']
assert saved['application_model']['integrated_version']=='v41';assert digest(project/saved['application_model']['path'])==baseline['application_model']['sha256']
print('ARCHIVED',archive,'verified deliverables',len(manifest),'public v41 model preserved')
