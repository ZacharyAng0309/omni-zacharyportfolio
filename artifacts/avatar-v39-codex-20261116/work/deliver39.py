from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
root=Path(__file__).resolve().parents[1];work=root/'work';out=root/'outputs';project=Path('D:/omni-workstation/projects/ZacharyPortfolio')
v=json.loads((work/'hair39-validation.json').read_text());bv=json.loads((work/'blend39-validation.json').read_text());seams=json.loads((work/'hair39-seams.json').read_text());assert v['checks_failed']==0 and bv['morph_meshes_synchronized']==6
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
canvas=Image.new('RGB',(1080,590),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,file) in enumerate([('Previous review — v38','portrait38-front.png'),('Surface and shading cleanup — v39','portrait39-front.png')]):
 canvas.paste(Image.open(work/file).convert('RGB').resize((540,540),Image.Resampling.LANCZOS),(i*540,50));draw.text((i*540+16,12),label,font=font,fill='white')
canvas.save(out/'avatar-v39-comparison.jpg',quality=93)
canvas=Image.new('RGB',(1080,810),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,file) in enumerate([('Previous side','portrait38-left.png'),('Refined side','portrait39-left.png'),('Refined back','portrait39-back.png'),('Neutral','expression39-neutral.png'),('Smile','expression39-smile.png'),('Blink + raised brow','expression39-blink-brow.png')]):
 x=i%3*360;y=i//3*405;im=Image.open(work/file).convert('RGB');im.thumbnail((360,360),Image.Resampling.LANCZOS);canvas.paste(im,(x+(360-im.width)//2,y+45));draw.text((x+12,y+10),label,font=font,fill='white')
canvas.save(out/'avatar-v39-review-views.jpg',quality=93)
report=f'''# Avatar v39 — side/rear hair and shading-seam cleanup

16 November 2026. **NO-SHIP:** Blender-verified review candidate. v38 remains the integrated application model.

## Changes retained

This pass follows the v38 hair refinement and the subsequent application integration recorded in the shared handoff. The supplied frontal portrait remains the likeness reference. Side/back shape is inferred; no independent likeness score is claimed.

- Local Laplacian relaxation moves {v['metrics']['hair_vertices_moved']} existing side/rear hair vertex copies by at most {v['metrics']['maximum_hair_movement_mm']:.3f} mm. The edit is bounded away from the frontal fringe and crown part, with every mesh boundary pinned. Triangle orientation and area are preserved. Some rear surface irregularity remains.
- Reconciled coincident UV-split normals in {seams['welded_groups']} compatible face/eyelid groups. {seams['by_mesh']['SM_Character_Face']} Face and {seams['by_mesh']['SM_Character_Eyelids']} Eyelids base normal copies changed. Groups use a 1 micrometre position tolerance and only combine vertices whose eight position targets remain coincident. Existing eyelid normal targets are adjusted consistently. This brings part of the runtime shading repair into the portable asset; it does not change face geometry or texture.
- Blender comparisons show less angular lip shading and modestly smoother side/back hair. The painted hairline and some cheek texture facets are still visible. The original seven embedded image payloads, all UVs, materials, topology, skin weights, joint transforms and all morph POSITION deltas remain byte-preserved.

Two trial previews added six tapered fringe locks. They looked like overlapping pieces and introduced visible shading/coverage artifacts. Those overlays and their new texture/material are **excluded** from the final candidate. The frontal fringe geometry is unchanged; this pass does not claim to have fixed its painted edge.

## Verification scope

- **{v['checks_passed']:,} checks passed, zero failed.** Scope: data preservation and finiteness, all seven original images, hair movement/boundary/triangle constraints, all 135 face/hair seam pairs, 252 repaired shading groups at rest and across eight target values, and resource budgets. This count includes repeated per-group normal continuity assertions, not independent visual judgments.
- Fresh exported GLB imported and rendered in Blender 5.2.2 from front, quarter, side, top and back. Facial review renders cover neutral, smile, speech, asymmetric speech, blink with raised brows, and quarter/side speech. Fourteen facial review keyframes remain available.
- Saved Blender review reopened: fourteen facial frames, six synchronized morph meshes, imported position-target values and packed images verified. Four gesture poses checked numerically on 198 sampled vertices each, below 0.001 mm difference. Prior eye visibility checks were not repeated because eye/lid positions, eye geometry and all position targets are unchanged.
- **Budgets:** {v['metrics']['triangles']:,} triangles; {v['metrics']['glb_bytes']:,} bytes; 52 joints; seven images, each below 100 KB. No additional mesh, texture, material, bone or morph channel is delivered.
- Current project WebGL governance audit passed with zero violations; candidate budgets checked separately. The v39 candidate has not been integrated or browser-tested. No application tests/build or VaultLinter release gate was rerun for this Blender-only pass.

The initial attempt was blocked by an approval-service usage limit. On 16 November the approved Blender run succeeded. The live add-on remained unavailable; installed Blender background rendering and saved-file inspection provided verification. No user assistance is needed for the saved review.

## QA verdict and next work

**NO-SHIP.** Remaining issues: the forehead/fringe texture transition, loose silhouette strands, coarse rear hair form, eye shading, facial texture fidelity, collar/wrist atlas margins and hand/cloth detail. The fringe requires an authored hairline/texture repair or a more complete groom; adding a few overlay locks was not sufficient.

The shared handoff reports v38 integrated and browser-verified with six-mesh facial synchronization, hair lighting adjustments, finger/rest-quaternion repairs and updated poses. The public v38 model is preserved (SHA-256 `ec703d9fe5ffd3f7af1109eef6e979fe5e50e1f72aff72ce4b6dcf357280f4a3`). Its prior integration record is retained in `work/resume39-baseline.json` in the v39 archive. v39 keeps the same schema-v4 six-mesh contract and adds no runtime requirements. Browser appearance must still be checked before substituting v39 in the app, particularly with its existing normal-welding and material overrides.

The GLB contains model/rig/morph data; Blender contains the review poses. v38 remains the rollback baseline. Application source and public model were not changed by this pass.
'''
(out/'Avatar-v39-Review.md').write_text(report,encoding='utf-8')
record=json.loads((work/'resume39-baseline.json').read_text(encoding='utf-8-sig'));assert record['latest_verified_review_version']=='v38'
record.update(latest_verified_review_version='v39',updated='2026-11-16',archive='artifacts/avatar-v39-codex-20261116',status='v39 Blender review verified; v38 remains integrated in the application; likeness/texture refinement ongoing')
names=['zachary_character_v39_candidate.glb','Zachary_Avatar_v39_Review.blend','avatar-v39-pose-targets.json','Avatar-v39-Review.md','avatar-v39-comparison.jpg','avatar-v39-review-views.jpg','full39-front.png','full39-audit.json']
record['files']={n:{'path':record['archive']+'/outputs/'+n,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in names}
record['changes']=['Bounded side/rear hair relaxation, maximum 1.601 mm; frontal fringe, crown part and boundaries retained.','252 compatible face/eyelid shading groups reconciled; less angular lip shading.','All topology, seven image payloads, UVs, weights and morph position deltas preserved; experimental fringe overlays excluded.']
record['verification']=['2588 preservation, geometry, shading-continuity and budget checks passed; zero failed.','Fresh GLB rendered at five angles and through seven facial review views; saved Blender review reopened.','Fourteen facial frames, six synchronized meshes, packed images and four gesture targets verified.','Current project governance audit passed; v39 application integration/browser checks pending.']
record['active_work']='v39 Blender review verifies side/rear hair relaxation and face/eyelid UV-split normal repair. Fringe overlay trials were rejected. Continue authored forehead/hairline texture repair and hair silhouette work. v38 remains integrated and browser-verified per the preserved application handoff; v39 is not integrated.'
record['application_model']['latest_candidate_integrated']=False
record['application_model']['verification_record']=record['archive']+'/work/resume39-baseline.json'
(work/'avatar-latest-v39.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified Blender review: **v39**, updated 16 November 2026 by Codex.','','**v38 remains integrated in the portfolio.** v39 is a Blender review candidate pending browser/application verification.','','## Files','']+[f'- [{n}]({record["files"][n]["path"]})' for n in names]
for title,field in [('Changes','changes'),('Verification','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+x for x in record[field]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'Prior v38 integration and runtime changes are preserved in ['+'application handoff]('+record['application_model']['verification_record']+'). GLB contains rig/morph data; review keyframes are in Blender. Preserve prior immutable archives.','']
(work/'AVATAR_LATEST-v39.md').write_text('\n'.join(lines),encoding='utf-8');print('DELIVERY_READY',len(names))
