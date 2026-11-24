from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[1];work=root/'work';project=Path('D:/omni-workstation/projects/ZacharyPortfolio');vault=Path('D:/omni-workstation/vault/01_Wiki/Projects/ZacharyPortfolio')
record=json.loads((work/'avatar-latest-v39.json').read_text());baseline=json.loads((work/'resume39-baseline.json').read_text(encoding='utf-8-sig'));current=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'))
assert current==baseline,'Concurrent handoff changes must be reconciled before archiving'
archive=(project/record['archive']).resolve();assert archive.is_relative_to((project/'artifacts').resolve());note=vault/'07_Documentation/avatar_v39_hair_shading_review.md';assert not archive.exists() and not note.exists()
assert json.loads((work/'hair39-validation.json').read_text())['checks_failed']==0
assert json.loads((work/'blend39-validation.json').read_text())['morph_meshes_synchronized']==6
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,data in record['files'].items():assert digest(root/'outputs'/name)==data['sha256']
assert digest(project/baseline['application_model']['path'])==baseline['application_model']['sha256']
(archive/'outputs').mkdir(parents=True);(archive/'work').mkdir();manifest=[]
for name,data in record['files'].items():
 dest=archive/'outputs'/name;shutil.copy2(root/'outputs'/name,dest);assert digest(dest)==data['sha256'];manifest.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest(dest),'verified':True})
shutil.copy2(root/'outputs/zachary_character_v38_candidate.glb',archive/'outputs/zachary_character_v38_candidate.glb')
names=['glb_asset.py','hair39-build.py','hair39-build.log','hair39-shape.glb','hair39-shape.json','hair39-seams.py','hair39-seams.json','hair39-seams.log','verify39.py','hair39-validation.json','prepare39-review.py','review39.py','whole39.py','rig39-review.py','rig39-review.json','expression39-review.py','expression39-review.log','finalize39.py','reopen39.py','blend39-validation.json','reopen39.log','build39.log','poses27.json','portrait38-front.png','portrait38-left.png','resume39-baseline.json','deliver39.py','archive39.py']
for name in names:shutil.copy2(work/name,archive/'work'/name)
for pattern in ['portrait39-*.png','expression39-*.png']:
 for path in work.glob(pattern):shutil.copy2(path,archive/'work'/path.name)
shutil.copy2(project/'src/graphics/SceneController.ts',archive/'work/SceneController-at-archive.ts')
(archive/'manifest.json').write_text(json.dumps(manifest,indent=2));(work/'archive39-validation.json').write_text(json.dumps(manifest,indent=2))
note.write_text('''---
id: DOC-ZacharyPortfolio-Avatar-v39-HairShading
title: Avatar side rear hair and shading seam cleanup review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, hair, face, review]
created_at: 2026-11-16
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'''+(root/'outputs/Avatar-v39-Review.md').read_text(encoding='utf-8'),encoding='utf-8')
index=vault/'07_Documentation/index.md';content=index.read_text(encoding='utf-8')
if 'avatar_v39_hair_shading_review' not in content:index.write_text(content+'\n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v39_hair_shading_review|Avatar v39 Side Rear Hair and Shading Seam Review]]\n',encoding='utf-8')
design=vault/'03_Design/persona_biometrics_and_likeness.md';content=design.read_text(encoding='utf-8')
if 'Side rear hair and split-normal cleanup - 16 November 2026' not in content:
 content+='''

## Side rear hair and split-normal cleanup - 16 November 2026

v39 retains bounded local Laplacian relaxation on 911 final side/rear hair vertex copies (maximum 1.601 mm) and reconciles 252 compatible coincident face/eyelid normal groups. Every hair boundary is pinned; front fringe/crown part and all 135 shared face/hair pairs are retained. Original UVs, topology, seven image payloads, rig weights, materials and morph position targets remain unchanged. Repaired normal groups remain continuous through all eight target values. Two small fringe-overlay trials were rejected as visually artificial and are excluded from the candidate. The forehead/fringe texture and loose-strand silhouette remain unfinished. v38 remains integrated in the portfolio; v39 is only a Blender review candidate pending browser checks.

Evidence and preserved application handoff: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v39_hair_shading_review]].
'''
 design.write_text(content,encoding='utf-8')
for source,name in [('AVATAR_LATEST-v39.md','AVATAR_LATEST.md'),('avatar-latest-v39.json','avatar-latest.json')]:shutil.copy2(work/source,archive/name);shutil.copy2(work/source,project/name)
saved=json.loads((project/'avatar-latest.json').read_text())
for data in saved['files'].values():assert digest(project/data['path'])==data['sha256']
assert saved['application_model']['integrated_version']=='v38'
assert digest(project/saved['application_model']['path'])==baseline['application_model']['sha256']
print('ARCHIVED',archive,'verified deliverables',len(manifest),'integrated application model preserved: v38')
