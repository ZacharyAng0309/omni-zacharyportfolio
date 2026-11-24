from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];work=root/'work';out=root/'outputs';v=json.loads((work/'eye36-validation.json').read_text());bv=json.loads((work/'blend36-validation.json').read_text());assert v['checks_failed']==0 and bv['morph_meshes_synchronized']==6
assert (work/'zachary_character_v36_eye_prototype.glb').read_bytes()==(out/'zachary_character_v36_candidate.glb').read_bytes()
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
canvas=Image.new('RGB',(1080,650),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,name) in enumerate([('Previous review — v35','expression35-neutral.png'),('Separate eyes and lids — v36','expression36-neutral.png')]):
 canvas.paste(Image.open(work/name).convert('RGB').resize((540,600),Image.Resampling.LANCZOS),(i*540,50));draw.text((i*540+16,12),label,font=font,fill='white')
canvas.save(out/'avatar-v36-comparison.jpg',quality=92)
canvas=Image.new('RGB',(1200,748),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,label in enumerate(['neutral','half-blink','blink','blink-brow','left-wink','right-wink','speech-quarter','speech-side']):
 x=i%4*300;y=i//4*374;canvas.paste(Image.open(work/f'expression36-{label}.png').convert('RGB').resize((300,333),Image.Resampling.LANCZOS),(x,y+41));draw.text((x+12,y+9),label.replace('-',' ').title(),font=font,fill='white')
canvas.save(out/'avatar-v36-expressions.jpg',quality=92)
report=f'''# Avatar v36 — separate eyes and fitted eyelids

14 November 2026. **NO-SHIP:** verified review candidate; likeness and website integration remain unfinished.

## Structural change

The former eyes were texture painted onto a continuous face surface. v36 replaces 277 triangles inside two local socket patches with real openings, a fitted eyelid mesh and two separate closed eye globes. The eyelid mesh has four concentric loops per eye, a transition into the original irregular boundary, and a thin inner rim. Skin color is baked from the existing face with Blender Cycles onto a new UV layout. The globes use dark pupil/iris and muted sclera vertex colors; these are artistic approximations, not a scan of personal eye anatomy.

Neutral opening height was reduced after the first prototype looked too wide-eyed. Existing outer-face blink targets gain depth movement so the lids pass over the globe surface. The new inner lid rings meet on a shared contact line; rim thickness is retained. Raised-brow influence tapers out before this contact line. Triangulation and float precision at the contact line were checked after export, fixing two folding quads and thin-rim artifacts found during iteration.

The original face rest positions, normals, UVs and skin weights are preserved. Six existing face targets are unchanged; only the two blink POSITION targets gain depth motion. Original materials and all six original image payloads remain unchanged. Ears, hair, glasses, hands, clothes and oral meshes retain their prior data. Three meshes are added: Eyelids, EyeLeft and EyeRight. The eyes follow Head and do not yet have independent gaze controls.

## Verification and limits

- **{v['checks_passed']} checks passed, zero failed.** Scope: original data/material/texture preservation, existing node transforms, finite arrays, weights/normals, original/new skin boundary correspondence for all eight targets, globe edge topology, texture/asset budgets, and sampled eye visibility.
- **Ten numeric eye cases:** neutral, quarter/half/three-quarter/full blink, full blink with raised brows, both winks, raised brows and speech. Zero eye samples protruded through skin outside the intended opening. Full blink and blink+brow hid every sampled globe point. These finite ray samples do not constitute an exhaustive surface-intersection proof.
- No zero-area eyelid triangles in checked poses; eyelid front triangles retain their projected orientation (the closed rim can turn edge-on). Combined Face + Eyelids + OralCavity has zero nonmanifold edges and exactly 64 additional boundary edges for the two intended eye openings. Other pre-existing skin boundaries remain; no claim that the whole character is watertight.
- Fresh exported GLB rendered in Blender: fourteen expression poses, quarter/side speech, portrait front/quarter and the full body. Four gesture poses were checked numerically. The saved Blender file was reopened: all fourteen facial frames synchronize **six** facial meshes; every imported morph vertex was compared with the GLB, images are packed, and gesture wrist errors remain below 0.001 mm.
- **Budgets:** {v['metrics']['triangles']:,} triangles; {v['metrics']['glb_bytes']:,} bytes; 52 joints. Seven image payloads, all below 100 KB. Eyelids: 345 vertices/537 triangles. Each closed eye globe: 290 vertices/576 triangles.
- Project WebGL governance audit passed with zero violations. It covers current project source/public assets; candidate budgets were checked separately. Application/browser integration, tests/build and VaultLinter release gates remain pending.

Blender 5.2.2 was run in the background. The live add-on connection was unavailable. No external generation service was used and no user assistance was needed for these checks.

## Visual assessment and next work

This is a structural eye upgrade with a noticeably different neutral appearance. It is not final photorealistic likeness. Iris variation/cornea appearance, pupil/iris proportions and upper-lid folds need further refinement against the portrait. The skin texture remains soft and contains inherited shading. Side/back anatomy is approximate with only the frontal reference available. Lip/cheek motion, oral detail, finger creasing and raised-elbow cloth also remain open work.

## Integration contract

`avatar-v36-pose-targets.json` uses **schema version 4**. Drive matching facial target values on Face, OralCavity, UpperTeeth, LowerTeeth, Tongue **and Eyelids**, resetting inactive values on all six each frame. Updating only the old five meshes will break blink closure. EyeLeft/EyeRight are head-skinned static globes and have no morph targets. Existing arm/finger pose rules remain applicable.

`Zachary_Avatar_v36_Review.blend` contains the portrait, whole-model gesture and facial-expression scenes. Facial markers span frames 1–521. The GLB contains rig and morph data; review timeline keyframes are stored in Blender. The public portfolio model and source are unchanged. Preserve the v35 archive as the rollback baseline.
'''
(out/'Avatar-v36-Review.md').write_text(report,encoding='utf-8')
project=Path('D:/omni-workstation/projects/ZacharyPortfolio');record=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert record['latest_verified_review_version']=='v35'
record.update(latest_verified_review_version='v36',updated='2026-11-14',archive='artifacts/avatar-v36-codex-20261114')
names=['zachary_character_v36_candidate.glb','Zachary_Avatar_v36_Review.blend','avatar-v36-pose-targets.json','Avatar-v36-Review.md','avatar-v36-comparison.jpg','avatar-v36-expressions.jpg','full36-front.png','full36-audit.json']
record['files']={n:{'path':record['archive']+'/outputs/'+n,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in names}
record['changes']=['Added real eye openings, four fitted lid loops per eye, and two separate closed eye globes.','Added outer-lid depth motion and verified closed-lid contact with raised brows.','Preserved source rest geometry, textures and non-blink targets; new six-mesh facial synchronization contract.']
record['verification']=[f"{v['checks_passed']} data, seam, topology, deformation, sampled visibility and budget checks passed; zero failed.",'Fresh exported GLB rendered across fourteen expressions and two speech angles; saved Blender review reopened successfully.','All six facial meshes, imported morph values, packed textures and gesture targets verified.','Current project governance audit passed with zero violations; release gates remain pending.']
record['next_work']=['Refine iris/cornea appearance, iris proportions and upper-lid folds against the portrait','Sharper face texture, lip/cheek motion and oral anatomy','Finger creasing and raised-elbow cloth','Six-mesh application integration, gaze controls, remaining poses and release gates']
record['active_work']='v36 structural eye/eyelid upgrade verified. Next focus: eye appearance and upper-lid likeness. IMPORTANT: schema-v4 facial animation must synchronize Eyelids along with the existing five meshes. The globes currently follow Head only.'
record['application_model']['latest_candidate_integrated']=False
(work/'avatar-latest-v36.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified review: **v36**, updated 14 November 2026 by Codex.','','Whole-model refinement remains in progress; not a production release.','','## Files','']+[f'- [{n}]({record["files"][n]["path"]})' for n in names]
for title,field in [('Changes','changes'),('Verification','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+s for s in record[field]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'The public portfolio model is unchanged. Application/browser and release checks remain pending. The GLB contains rig/morph data; review keyframes are in the Blender file. Preserve prior immutable archives.','']
(work/'AVATAR_LATEST-v36.md').write_text('\n'.join(lines),encoding='utf-8');print('DELIVERY_READY',len(names))
