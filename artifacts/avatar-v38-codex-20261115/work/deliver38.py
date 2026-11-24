from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
root=Path(__file__).resolve().parents[1];work=root/'work';out=root/'outputs';project=Path('D:/omni-workstation/projects/ZacharyPortfolio')
v=json.loads((work/'hair38-validation.json').read_text());bv=json.loads((work/'blend38-validation.json').read_text());shape=json.loads((work/'hair38-shape.json').read_text());tex=json.loads((work/'hair38-textures.json').read_text())
assert v['checks_failed']==0 and bv['morph_meshes_synchronized']==6
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
canvas=Image.new('RGB',(1080,590),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,file) in enumerate([('Previous hair — v37','portrait37-front.png'),('Refined part and strands — v38','portrait38-front.png')]):
 canvas.paste(Image.open(work/file).convert('RGB').resize((540,540),Image.Resampling.LANCZOS),(i*540,50));draw.text((i*540+16,12),label,font=font,fill='white')
canvas.save(out/'avatar-v38-comparison.jpg',quality=93)
canvas=Image.new('RGB',(1080,810),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,file) in enumerate([('Front','portrait38-front.png'),('Quarter','portrait38-quarter.png'),('Side','portrait38-left.png'),('Top','portrait38-top.png'),('Back','portrait38-back.png'),('Blink + raised brow','expression38-blink-brow.png')]):
 x=i%3*360;y=i//3*405;im=Image.open(work/file).convert('RGB');im.thumbnail((360,360),Image.Resampling.LANCZOS);canvas.paste(im,(x+(360-im.width)//2,y+45));draw.text((x+12,y+10),label,font=font,fill='white')
canvas.save(out/'avatar-v38-hair-views.jpg',quality=93)
report=f'''# Avatar v38 — crown part and hair strands

15 November 2026. **NO-SHIP:** verified review candidate; likeness and website integration remain unfinished.

## Result and reference assessment

The original frontal portrait shows dark brown curtain hair, a slightly offset part, a fuller right lobe and fine strand groups. v37 had a broadly compatible mass but a continuous cap-like surface. v38 introduces a soft crown-part dip and more legible combed strand groups. These are artistic adjustments from a single frontal photo; side/back grooming remains inferred. No calibrated likeness or biometric score is claimed.

- Proportional crown edit: {shape['affected_vertex_copies']} existing hair vertex copies, maximum {shape['max_displacement_mm']:.3f} mm downward movement. No new geometry. Every hair boundary vertex is pinned, including all 135 matched face/hair seam pairs. Minimum triangle orientation cosine {shape['minimum_triangle_orientation_cosine']:.3f}; minimum area ratio {shape['minimum_area_ratio']:.3f}.
- Three scales of directional lock/strand detail flow from a pole tilted toward the frontal part. Warm dark brown color variation, a restrained bump and strand-varying roughness break up the previous smooth surface. A texture-content mask and seam falloff protect skin and the garment patch carried in the original Hair mesh.
- Native Cycles baking uses the existing second UV map. Only the three hair image payloads are replaced: 2048² albedo, 1024² tangent normal and 512² packed roughness/specular. No image generation or external generation service was used.
- The first fine-strand bake lost too much detail. The final material uses a coarser strand scale that remains legible after baking. Normal-map compression has {tex['normal']['angular_error_degrees_percentiles'][1]:.2f}° 95th-percentile error against the raw bake, {tex['normal']['angular_error_degrees_percentiles'][2]:.2f}° at the 99th percentile; boundary outliers remain. Parameter quantization is bounded by {tex['parameters']['maximum_scalar_quantization_error']:.5f}. The normal map now uses EXT_texture_webp, already required by the avatar; browser appearance is still unverified.

## Verification scope

- **337 checks passed, zero failed:** all accessors finite; all except hair POSITION/NORMAL byte-preserved; mesh topology, UVs, skin weights, node/rig transforms, facial targets and unrelated materials preserved; four unrelated image payloads unchanged; seam coincidence, part movement, normals, triangle orientation/area and budgets checked.
- Fresh exported GLB imported into Blender 5.2.2 and rendered from front, quarter, side, top and back. Additional fresh-import facial renders cover neutral, speech, blink with raised brows, and quarter/side speech. Broad rim highlights and residual side/rear surface lumps are still visible; this is not a strand-based groom.
- All fourteen facial poses are retained as review keyframes. The saved Blender file was reopened and all fourteen frames checked across six synchronized facial meshes. Imported morph vertex deltas and packed images verified. Four gesture poses checked numerically, 198 sampled vertices per pose, maximum difference below 0.001 mm. Body/eye geometry was unchanged, so the previous exhaustive eye visibility test was not repeated.
- **Budgets:** {v['metrics']['triangles']:,} triangles; {v['metrics']['glb_bytes']:,} bytes; 52 joints; seven images, each below 100 KB. Current project WebGL governance audit passed with zero violations; it covers project source/public files, while candidate budgets were checked separately.

The live Blender add-on was unavailable; all creation, rendering and saved-file verification used the installed Blender in background mode. No user assistance was required for this pass.

## QA verdict and remaining work

**NO-SHIP.** The part and directional strands are more distinct, but the fringe still has a jagged painted/mesh transition. Loose silhouette strands, a less uniform comb pattern and side/rear volume need more work. Fine hair detail can soften at portfolio camera distance. The original face texture, eye shading, subtle asymmetry and hand/cloth details also remain unfinished.

Untested release gates: browser/Three.js appearance and integration, application tests/build, VaultLinter, and independent side/back likeness. A quantitative image-match score was not used because the reference and review differ in clothing, framing and lighting.

The schema-v4 pose file still requires synchronized morph values on Face, OralCavity, UpperTeeth, LowerTeeth, Tongue and Eyelids; both globes follow Head. The GLB contains mesh/rig/morph data, while the fourteen facial and four gesture review keyframes are stored in Blender. Public portfolio assets and application source are unchanged. v37 remains the rollback baseline.
'''
(out/'Avatar-v38-Review.md').write_text(report,encoding='utf-8')
record=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert record['latest_verified_review_version']=='v37'
record.update(latest_verified_review_version='v38',updated='2026-11-15',archive='artifacts/avatar-v38-codex-20261115')
names=['zachary_character_v38_candidate.glb','Zachary_Avatar_v38_Review.blend','avatar-v38-pose-targets.json','Avatar-v38-Review.md','avatar-v38-comparison.jpg','avatar-v38-hair-views.jpg','full38-front.png','full38-audit.json']
record['files']={n:{'path':record['archive']+'/outputs/'+n,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in names}
record['changes']=['Soft crown-part dip, maximum 5.448 mm; 130 existing hair vertices adjusted.','Directional brown strand groups with newly baked albedo, normal and roughness/specular maps.','All shared hair/face boundaries, topology, weights, facial targets and unrelated materials preserved.']
record['verification']=['337 geometry, preservation and budget checks passed; zero failed.','Fresh GLB rendered from five hair angles and during facial motion; saved Blender review reopened.','Fourteen facial frames, six synchronized meshes, packed textures and four gesture targets verified.','Current project governance audit passed; application integration and release gates remain pending.']
record['next_work']=['Fringe edge cleanup, loose silhouette strands and less uniform strand flow','Side/back hair surface refinement; one frontal reference limits likeness','Eye shading, face texture, lip/cheek motion and hand/cloth detail','Six-mesh application integration, browser appearance and release gates']
record['active_work']='v38 crown-part and baked strand refinement verified. Hair remains a review candidate, with jagged fringe edges and side/rear lumps still visible. Continue silhouette/fringe cleanup. Schema-v4 animation must synchronize all six facial meshes. Public application model unchanged.'
record['application_model']['latest_candidate_integrated']=False
(work/'avatar-latest-v38.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified review: **v38**, updated 15 November 2026 by Codex.','','Whole-model refinement remains in progress; not a production release.','','## Files','']+[f'- [{n}]({record["files"][n]["path"]})' for n in names]
for title,field in [('Changes','changes'),('Verification','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+x for x in record[field]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'GLB contains rig/morph data; review keyframes are in Blender. Preserve prior immutable archives.','']
(work/'AVATAR_LATEST-v38.md').write_text('\n'.join(lines),encoding='utf-8');print('DELIVERY_READY',len(names))
