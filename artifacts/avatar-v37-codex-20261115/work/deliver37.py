from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];work=root/'work';out=root/'outputs';v=json.loads((work/'eye37-validation.json').read_text());bv=json.loads((work/'blend37-validation.json').read_text());assert v['checks_failed']==0 and bv['morph_meshes_synchronized']==6
assert (work/'zachary_character_v37_tuning.glb').read_bytes()==(out/'zachary_character_v37_candidate.glb').read_bytes()
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
canvas=Image.new('RGB',(1080,650),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,name) in enumerate([('Previous review — v36','expression36-neutral.png'),('Eye likeness tuning — v37','expression37-neutral.png')]):
 canvas.paste(Image.open(work/name).convert('RGB').resize((540,600),Image.Resampling.LANCZOS),(i*540,50));draw.text((i*540+16,12),label,font=font,fill='white')
canvas.save(out/'avatar-v37-comparison.jpg',quality=92)
canvas=Image.new('RGB',(1200,748),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,label in enumerate(['neutral','half-blink','blink','blink-brow','left-wink','right-wink','speech-quarter','speech-side']):
 x=i%4*300;y=i//4*374;canvas.paste(Image.open(work/f'expression37-{label}.png').convert('RGB').resize((300,333),Image.Resampling.LANCZOS),(x,y+41));draw.text((x+12,y+9),label.replace('-',' ').title(),font=font,fill='white')
canvas.save(out/'avatar-v37-expressions.jpg',quality=92)
report=f'''# Avatar v37 — eye placement, iris and lid tuning

15 November 2026. **NO-SHIP:** Blender-verified review candidate; likeness and website integration remain unfinished.

## Change and reference assessment

The supplied frontal portrait was inspected beside v36, including a magnified eye crop. v36 had a relatively flat horizontal opening, large dark pupil and high eye line within the frames. v37 tests a lower assembly, a fuller visible iris and a restrained corner angle. These are artist-guided adjustments from a single photo, not calibrated biometric measurements or a verified likeness score.

- Lowered the eyes by 1.6 mm with proportional support in the surrounding face and a small fringe region. This changes Y positions only on Face/Hair. All 135 original hair/face seam pairs remain coincident.
- Changed pupil radius from 2.5 to 2.0 mm and iris radius from 5.3 to 5.8 mm. The globe's outer silhouette is retained. Warm brown vertex colors replace the previous iris colors; no texture was generated or repainted.
- Added up to 0.8 mm lateral widening and a modest outer-corner lift to the inner lid loops, with a fuller lower arc and a 0.2 mm upper-lid crease. The neutral lid fit changes while its previous closed endpoint is preserved before translating the eye assembly.
- Reduced the eye material's broad reflection (specular factor 0.20 to 0.10, roughness 0.23 to 0.14). Front and quarter renders show a lower eye line and less of the thin horizontal slit from v36. The result remains stylized.

The edit preserves topology, UVs, seven embedded image payloads, skin weights, node transforms and the six-part facial target contract. All original Face morph deltas are preserved; eyelid blink POSITION targets and eyelid NORMAL targets are updated for the revised neutral shape. Unrelated materials and meshes remain unchanged, including the active oral surface. The eye-support displacement also affects 51 hair vertex copies; this is documented rather than treated as an eyes-only buffer edit.

## Verification scope

- **{v['checks_passed']} checks passed, zero failed.** Scope: preserved accessors, textures, scene structure, weights, local placement bounds, face/hair seams, active oral vertices, and all eight target values at each original eyelid/face boundary point.
- **Ten numeric eye cases:** neutral, quarter/half/three-quarter/full blink, blink with raised brows, both winks, raised brows and speech. No sampled globe point protrudes through skin outside the intended opening. Full blink and blink+brow hide every sampled globe point. Finite ray samples are not an exhaustive continuous intersection proof.
- Eyelid front orientation and nonzero triangle area remain valid in checked cases. The two globes retain closed topology. Face + Eyelids + OralCavity retain the same edge multiplicities as v36, including the two intended eye apertures; the whole character is not claimed watertight.
- Fresh GLB imported and rendered in Blender: fourteen expressions, quarter/side speech, portrait front/quarter and full body. Four gesture poses checked numerically. The saved Blender file was reopened: fourteen facial frames synchronize six meshes; imported morph vertices, packed images and gesture wrist targets verified.
- **Budgets:** {v['metrics']['triangles']:,} triangles; {v['metrics']['glb_bytes']:,} bytes; 52 joints. Seven image payloads, each below 100 KB. No added polygons or textures.
- Current project WebGL governance audit passed with zero violations. It covers current project source/public assets; candidate budgets were checked separately. Application/browser integration, tests/build and VaultLinter release gates remain pending.

Blender 5.2.2 ran in the background; the live add-on connection was unavailable. No external generation service was used, and no assistance was required to complete this pass.

## Remaining work and integration

The iris/cornea shading and lid transitions still look simplified. Subtle asymmetry, tear ducts and more faithful skin detail remain open likeness work. No independent gaze rig exists. A single frontal image limits accurate side/back reconstruction. Lip/cheek motion, oral detail, finger creasing and raised-elbow cloth also remain unfinished.

The schema-version-4 pose file still requires matching target values on **Face, OralCavity, UpperTeeth, LowerTeeth, Tongue and Eyelids**, resetting inactive values on all six each frame. EyeLeft/EyeRight follow Head without morph targets. Updating only the old five facial meshes breaks blink closure.

`Zachary_Avatar_v37_Review.blend` contains portrait, full-body gesture and facial-expression scenes; facial markers span frames 1–521. The GLB contains mesh, rig and morph data; review keyframes are stored in Blender. The public portfolio model and application source are unchanged. Preserve v36 as the rollback baseline.
'''
(out/'Avatar-v37-Review.md').write_text(report,encoding='utf-8')
project=Path('D:/omni-workstation/projects/ZacharyPortfolio');record=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert record['latest_verified_review_version']=='v36'
record.update(latest_verified_review_version='v37',updated='2026-11-15',archive='artifacts/avatar-v37-codex-20261115')
names=['zachary_character_v37_candidate.glb','Zachary_Avatar_v37_Review.blend','avatar-v37-pose-targets.json','Avatar-v37-Review.md','avatar-v37-comparison.jpg','avatar-v37-expressions.jpg','full37-front.png','full37-audit.json']
record['files']={n:{'path':record['archive']+'/outputs/'+n,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in names}
record['changes']=['Lowered eye assembly by 1.6 mm with local support; shared skin/hair boundaries maintained.','Smaller pupils, larger warm brown irises, angled/full lid openings and a restrained upper-lid crease.','Preserved topology, images, UVs, weights, original Face targets and the schema-v4 six-mesh contract.']
record['verification']=[f"{v['checks_passed']} preservation, geometry, seam, sampled visibility and budget checks passed; zero failed.",'Fresh GLB rendered across fourteen expressions and quarter/side views; saved Blender review reopened.','All six facial meshes, imported morph values, packed textures and gesture targets verified.','Current project governance audit passed; application and release gates pending.']
record['next_work']=['More natural iris/cornea shading, subtle eye asymmetry and tear ducts','Sharper facial detail and lip/cheek motion','Finger creasing and raised-elbow cloth','Six-mesh application integration, gaze controls, remaining poses and release gates']
record['active_work']='v37 eye placement, iris proportions and lid tuning verified. Likeness remains a review candidate. Continue eye/skin realism and subtle asymmetry. Schema-v4 animation must synchronize Eyelids with the five other facial meshes; globes follow Head only.'
record['application_model']['latest_candidate_integrated']=False
(work/'avatar-latest-v37.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified review: **v37**, updated 15 November 2026 by Codex.','','Whole-model refinement remains in progress; not a production release.','','## Files','']+[f'- [{n}]({record["files"][n]["path"]})' for n in names]
for title,field in [('Changes','changes'),('Verification','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+s for s in record[field]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'Public portfolio model unchanged. Application/browser and release checks remain pending. GLB contains rig/morph data; review keyframes are in Blender. Preserve prior immutable archives.','']
(work/'AVATAR_LATEST-v37.md').write_text('\n'.join(lines),encoding='utf-8');print('DELIVERY_READY',len(names))
