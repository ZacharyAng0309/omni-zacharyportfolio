from pathlib import Path
import shutil,json,hashlib
root=Path(__file__).resolve().parents[1];project=Path('D:/omni-workstation/projects/ZacharyPortfolio');work=root/'work'
vault=Path('D:/omni-workstation/vault/01_Wiki/Projects/ZacharyPortfolio');note=vault/'07_Documentation/avatar_v34_eye_review.md'
record=json.loads((work/'avatar-latest-v34.json').read_text());current=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'))
assert current['latest_verified_review_version']=='v33','Shared latest record changed; re-read first'
archive=(project/record['archive']).resolve();assert archive.is_relative_to((project/'artifacts').resolve())
assert not archive.exists() and not note.exists(),'Preserve immutable archive'
v=json.loads((work/'eye34-validation.json').read_text());b=json.loads((work/'blend34-validation.json').read_text());assert v['checks_failed']==0 and b['morph_meshes_synchronized']==5
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for name,entry in record['files'].items():assert digest(root/'outputs'/name)==entry['sha256']
assert digest(project/'public/models/zachary_character.glb')=='df73e3ad3c62e935962ef6cf82491ccb725a17c82ca0284711fd50b8d647ac08'
(archive/'outputs').mkdir(parents=True);(archive/'work').mkdir()
manifest=[]
for name,entry in record['files'].items():
 src=root/'outputs'/name;dest=archive/'outputs'/name;shutil.copy2(src,dest);assert digest(dest)==entry['sha256'];manifest.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest(dest),'verified':True})
shutil.copy2(root/'outputs/zachary_character_v33_candidate.glb',archive/'outputs/zachary_character_v33_candidate.glb')
names=['glb_asset.py','eye34-cdt-probe.py','eye34-retopo.npz','eye34-bake.py','eye34-baked-data.npz','eye34-albedo.png','eye34-export.py','eye34-blink.py','eye34-blink-changes.json','eye34-changes.json','eye34-duplicate-sources.npy','verify34.py','eye34-validation.json','review34.py','whole34.py','rig34-review.py','rig34-review.json','expression34-review.py','expression34-review.log','finalize34.py','reopen34.py','blend34-validation.json','build34.log','poses27.json','deliver34.py','archive34.py']
for name in names:shutil.copy2(work/name,archive/'work'/name)
for p in work.glob('expression34-*.png'):shutil.copy2(p,archive/'work'/p.name)
shutil.copy2(project/'src/graphics/SceneController.ts',archive/'work/SceneController-at-review.ts')
(archive/'manifest.json').write_text(json.dumps(manifest,indent=2));(work/'archive34-validation.json').write_text(json.dumps(manifest,indent=2))
frontmatter='''---
id: DOC-ZacharyPortfolio-Avatar-v34-Eyes
title: Avatar eye topology and blink review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, rig, face, review]
created_at: 2026-11-13
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'''
note.write_text(frontmatter+(root/'outputs/Avatar-v34-Review.md').read_text(encoding='utf-8'),encoding='utf-8')
index=vault/'07_Documentation/index.md';content=index.read_text(encoding='utf-8')
if 'avatar_v34_eye_review' not in content:index.write_text(content+'\n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v34_eye_review|Avatar v34 Eye Surface Review]]\n',encoding='utf-8')
design=vault/'03_Design/persona_biometrics_and_likeness.md';content=design.read_text(encoding='utf-8')
if 'Eye surface review - 13 November 2026' not in content:
 content+='''

## Eye surface review - 13 November 2026

v34 removes three nonmanifold edges from two eye patches by retriangulating existing surface points. Boundary edges, rest shape and non-blink targets are preserved. Blink corrections under 0.03 mm prevent patch inversions in reviewed blink/brow combinations. A whole-face unwrap caused UV overlap near nose and mouth, so the delivered atlas preserves original sampling on unchanged triangles and isolates baked eye patches. This reduces the right-eye fold but does not create anatomical eyelids or improve the low-detail source portrait texture. The whole model remains a review candidate.

Evidence and limitations: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v34_eye_review]].
'''
 design.write_text(content,encoding='utf-8')
for src,name in [('avatar-latest-v34.json','avatar-latest.json'),('AVATAR_LATEST-v34.md','AVATAR_LATEST.md')]:
 shutil.copy2(work/src,archive/name);shutil.copy2(work/src,project/name)
saved=json.loads((project/'avatar-latest.json').read_text())
for entry in saved['files'].values():assert digest(project/entry['path'])==entry['sha256']
print('ARCHIVED',archive,'verified deliverables',len(manifest))
