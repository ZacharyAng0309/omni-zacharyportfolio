from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];work=root/'work';out=root/'outputs'
v=json.loads((work/'verify35.json').read_text());bv=json.loads((work/'blend35-validation.json').read_text());assert v['checks_failed']==0 and bv['morph_meshes_synchronized']==5
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
canvas=Image.new('RGB',(1080,650),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,name) in enumerate([('Previous review — v34','expression34-neutral.png'),('Brow/fringe cleanup — v35','expression35-neutral.png')]):
 canvas.paste(Image.open(work/name).convert('RGB').resize((540,600),Image.Resampling.LANCZOS),(i*540,50));draw.text((i*540+16,12),label,font=font,fill='white')
canvas.save(out/'avatar-v35-comparison.jpg',quality=92)
canvas=Image.new('RGB',(1200,748),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,label in enumerate(['neutral','half-blink','blink','blink-brow','left-wink','right-wink','speech-quarter','speech-side']):
 x=i%4*300;y=i//4*374;canvas.paste(Image.open(work/f'expression35-{label}.png').convert('RGB').resize((300,333),Image.Resampling.LANCZOS),(x,y+41));draw.text((x+12,y+9),label.replace('-',' ').title(),font=font,fill='white')
canvas.save(out/'avatar-v35-expressions.jpg',quality=92)
canvas=Image.new('RGB',(1200,650),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,label in enumerate(['before','after']):
 canvas.paste(Image.open(work/f'clay35-{label}-quarter.png').convert('RGB').resize((600,600),Image.Resampling.LANCZOS),(i*600,50));draw.text((i*600+20,12),label.title()+' — geometry only',font=font,fill='white')
canvas.save(out/'avatar-v35-geometry.jpg',quality=92)
report=f'''# Avatar v35 — brow and fringe surface cleanup

13 November 2026. **NO-SHIP:** verified review candidate; whole-model likeness refinement remains in progress.

## Change and observed result

This is a subtle local surface cleanup, not a new anatomical eye model. A constrained Laplacian pass relaxes the forehead/brow-to-fringe transition, with updated surface normals. Front and quarter clay renders and textured portraits were inspected in Blender. The change is small at normal portrait size; the soft source textures and simplified eyes remain clearly visible limitations.

The edit moves 164 face vertex copies and 271 hair vertex copies by at most 0.901 mm (including float rounding). The two surfaces are relaxed together so all 135 original shared seam pairs remain exactly coincident. Bounding-box extrema are fixed. The ear region, lower face, glasses, clothes, hands, skin weights, topology, UVs, materials, all six embedded texture payloads and every morph delta remain unchanged. Every face vertex participating in blinking keeps its original rest position.

## Verification scope

- **{v['checks_passed']} checks passed, zero failed:** unchanged accessors and scene structure, texture payload preservation and budgets, finite data, unit normals, bounded/localized displacement, original hair/face seams, combined edge multiplicities, and active oral-surface preservation.
- **Fourteen numeric deformation cases** checked for the modified face and hair: neutral, all eight individual targets, blink+brow, half-blink, speech, smile/speech and wide mouth. No new orientation reversals or triangles collapsing below half their baseline area. The v34 repaired eye patches also retain positive front-facing orientation in the relevant stress cases.
- **Fresh Blender renders:** front and quarter portraits; front and quarter clay comparisons; neutral, blink, half blink, left wink, right wink, blink+brow, and quarter/side speech. The full body was rendered and four gesture poses were checked numerically.
- **Saved Blender file reopened:** all 14 expression timeline frames synchronize all five facial meshes; every imported morph vertex is checked against the GLB; 12 image datablocks are packed. Gesture wrist errors remain below 0.001 mm.
- **Budgets:** {v['metrics']['triangles']:,} triangles, {v['metrics']['glb_bytes']:,} bytes, 52 joints, all six textures below 100 KB. No polygon or texture budget increase from v34.
- Current project WebGL governance audit passed with zero violations. This audit covers current project source/public assets; candidate budgets were checked separately. Application tests/build, browser integration and VaultLinter release gates are pending.

Blender 5.2.2 ran in the background because the live add-on connection was unavailable. No assistance was required to complete these checks. No external generation service was used.

## Remaining work

Anatomical eyelid loops and separate eye anatomy remain the main improvement needed in this area. Further small smoothing passes will have diminishing visual benefit. Sharper facial texture, a cleaner fringe transition, lip/cheek motion, finger creasing and raised-elbow cloth also remain open. A frontal reference alone does not establish accurate side/back likeness. This version does not claim photorealism or final portfolio readiness.

## Review files and integration

`Zachary_Avatar_v35_Review.blend` includes portrait, whole-model gesture and facial-expression scenes. Facial markers run from frame 1 to 521. `zachary_character_v35_candidate.glb` contains the mesh, rig and morph data. `avatar-v35-pose-targets.json` retains the schema-version-3 contract for five synchronized facial meshes. The GLB does not contain the review timeline animation.

Drive matching targets on Face, OralCavity, UpperTeeth, LowerTeeth and Tongue; reset inactive values on all five. Existing arm targets and the cached rest quaternion multiplied by local-X finger curl remain applicable. Preserve the v34 archive. The public portfolio model and application source have not been replaced.
'''
(out/'Avatar-v35-Review.md').write_text(report,encoding='utf-8')
project=Path('D:/omni-workstation/projects/ZacharyPortfolio');record=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert record['latest_verified_review_version']=='v34'
record.update(latest_verified_review_version='v35',updated='2026-11-13',archive='artifacts/avatar-v35-codex-20261113')
names=['zachary_character_v35_candidate.glb','Zachary_Avatar_v35_Review.blend','avatar-v35-pose-targets.json','Avatar-v35-Review.md','avatar-v35-comparison.jpg','avatar-v35-expressions.jpg','avatar-v35-geometry.jpg','full35-front.png','full35-audit.json']
record['files']={n:{'path':record['archive']+'/outputs/'+n,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in names}
record['changes']=['Sub-millimeter local brow/fringe relaxation; visual change is subtle.','All 135 original shared hair/face seam pairs remain coincident; bounding extrema and blink-active rest vertices are fixed.','Topology, UVs, textures, materials, skin weights and all facial target deltas remain unchanged.']
record['verification']=[f"{v['checks_passed']} preservation, seam, local geometry, deformation and budget checks passed; zero failed.",'Fresh Blender portrait/clay comparisons and eight expression/angle renders inspected.','Saved Blender file reopened: fourteen expression frames, five synchronized facial meshes, packed textures, morph data and gesture positions verified.','Current project governance audit passed with zero violations; release gates remain pending.']
record['next_work']=['Build anatomical eyelid loops and eye anatomy; further smoothing has limited benefit','Sharper facial texture and a cleaner fringe transition','Lip/cheek motion, finger creasing and raised-elbow cloth','Remaining station poses, application integration and release gates']
record['active_work']='v35 subtle brow/fringe cleanup verified. Next priority is anatomical eye/eyelid reconstruction and facial texture; avoid accumulating small smoothing-only versions. Five facial meshes must remain synchronized.'
record['application_model']['latest_candidate_integrated']=False
(work/'avatar-latest-v35.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified review: **v35**, updated 13 November 2026 by Codex.','','Whole-model refinement remains in progress; not a production release.','','## Files','']+[f'- [{n}]({record["files"][n]["path"]})' for n in names]
for title,field in [('Changes','changes'),('Verification','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+s for s in record[field]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'The public portfolio model is unchanged. Application/browser and release checks remain pending. The GLB contains rig/morph data; review keyframes are in the Blender file. Preserve all prior immutable archives.','']
(work/'AVATAR_LATEST-v35.md').write_text('\n'.join(lines),encoding='utf-8');print('DELIVERY_READY',len(names))
