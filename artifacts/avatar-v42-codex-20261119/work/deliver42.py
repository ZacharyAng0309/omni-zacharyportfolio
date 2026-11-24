from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
root=Path(__file__).resolve().parents[1];work=root/'work';out=root/'outputs'
v=json.loads((work/'hair42-validation.json').read_text());bv=json.loads((work/'blend42-validation.json').read_text());hv=json.loads((work/'hair42-blender-validation.json').read_text())
assert v['checks_failed']==0 and bv['morph_meshes_synchronized']==6
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
canvas=Image.new('RGB',(1440,770),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,file) in enumerate([('v41 — before','hair42-baseline-front.png'),('v42 — crown and fine-strand refinement','portrait42-front.png')]):
 canvas.paste(Image.open(work/file).convert('RGB'),(i*720,50));draw.text((i*720+16,12),label,font=font,fill='white')
canvas.save(out/'avatar-v42-comparison.jpg',quality=95)
views=[('Front','portrait42-front.png'),('Quarter','portrait42-quarter.png'),('Side','portrait42-left.png'),('Crown','portrait42-top.png'),('Smile','expression42-smile.png'),('Blink + raised brow','expression42-blink-brow.png'),('Speech','expression42-speech-quarter.png'),('Asymmetric speech','expression42-asymmetric-speech.png')]
canvas=Image.new('RGB',(1440,890),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,file) in enumerate(views):
 x=i%4*360;y=i//4*445;im=Image.open(work/file).convert('RGB');im.thumbnail((360,400),Image.Resampling.LANCZOS);canvas.paste(im,(x+(360-im.width)//2,y+45));draw.text((x+10,y+10),label,font=font,fill='white')
canvas.save(out/'avatar-v42-review-views.jpg',quality=94)
report=f'''# Avatar v42 — crown and fine-strand refinement

19 November 2026. **NO-SHIP as a production update:** verified Blender review candidate. The integrated application remains v41.

## Result

This is a subtle hair finishing pass based on Antigravity's integrated v41. Local Laplacian relaxation softens small crown facets, moving {v['metrics']['crown_vertices_moved']} hair vertex copies by at most {v['metrics']['crown_max_displacement_mm']:.3f} mm. The lower fringe geometry and every original Face/Hair seam position remain fixed. The v41 face/chin, eyes, eyelids, spectacles, ears, skin textures, original rig weights and facial morph data are preserved.

Thirty-eight sparse round filaments add fine fringe ends and crown flyaways: 28 along the existing curtain fringe and 10 over the crown. Their widths taper toward the tips; roots embed into the existing surface. They use opaque vertex colors, smooth normals, and nearest-surface barycentric skin-weight transfer. All 1,256 new vertices follow the existing Head joint exactly. There is no alpha layer, texture-resolution increase, new image, bone or facial channel.

The added mesh is `SM_Character_HairFilaments`, with `M_Hair_Filaments_v42`. It adds 2,360 triangles and one material/draw call. The first thicker/darker strand trial was rejected during the Blender comparison; only the finer final version is included. The overall hairstyle is still stylized and the underlying painted fringe remains. This does not constitute a full groom or a calibrated likeness match. The original front photograph guided the part and flow; crown/side depth is inferred from one view.

## Verification scope

- **{v['checks_passed']} preservation, geometry and rig checks passed; zero failed.** Every original accessor is byte-equivalent as decoded except the crown's Hair position/normal arrays. All original materials, textures, seven embedded image payloads, UV sets, joint data, morph targets and mesh definitions are retained. The 155 Face/Hair seam vertex copies retain their positions.
- The new filaments are closed manifold tubes, with consistent outward winding, positive enclosed volumes, unit normals, nondegenerate triangles, valid indices and normalized skin weights. Original hair triangles retain orientation and bounded area ratios.
- Fresh exported GLB imported into Blender and rendered from front, quarter, side, top and back. Facial renders cover neutral, smile, speech, asymmetric speech, blink with raised brows, and quarter/side speech. Identical lighting and cameras provide the v41/v42 comparison. Live Blender MCP remained unavailable; Blender 5.2.2 background rendering and file reopen supplied the verification.
- The final `.blend` reopened with all fourteen facial frames synchronized across six meshes, all imported morph positions verified, fourteen packed image datablocks, and four gesture poses checked. Gesture samples and wrist-target comparisons remained below 0.001 mm.
- Head-yaw and pitch checks tested every imported filament vertex across three rotations: maximum difference from the expected Head transform was {max(row['maximum_error_mm'] for row in hv['head_rotation_checks'].values()):.6f} mm. The exposed distal fringe was sampled at {hv['raised_brow_distal_fringe_samples']} points against the fully raised-brow forehead; the conservative minimum clearance was {hv['conservative_minimum_forehead_clearance_mm']:.3f} mm. This is a sampled clearance check, not a continuous collision proof.
- **Budgets:** {v['metrics']['triangles']:,} triangles; {v['metrics']['glb_bytes']:,} bytes; 52 joints; seven images, all below 100 KB. The candidate is below 3.0 MB. The project WebGL governance audit passed with zero violations.

## Remaining work and integration limits

The browser-integrated v41 is unchanged. v42 has not been checked in the application's lighting, anti-aliasing or device performance. The existing application applies its special hair material calibration only to the exact `SM_Character_Hair` mesh name; evaluate the new `SM_Character_HairFilaments` material under that lighting before integration. Fine fibers may require distance-dependent visibility or an LOD policy. Application tests/build and VaultLinter release gates were not rerun for this Blender-only pass.

Broader hair clump volume and fringe outline, native collar/wrist atlas margins, residual skin/cloth facets, and hand detail remain refinement work. The raw Blender GLB still shows the inherited collar atlas triangles that v41's application shader masks; this pass does not claim to repair that asset-level issue. No Higgsfield or image-generation service was used.

## Handoff

The archive contains the v41 rollback GLB, authored strand paths/mesh arrays, build and verification scripts, source-state snapshot, final renders and saved Blender review. Reproduction: `hair42-build.py` in Blender → `hair42-embed.py` → `verify42.py` → fresh Blender import/render → expression/whole-model review → saved-file reopen. Base-color UV2 and normal/parameter UV1 remain unchanged. Pose schema v4 and its six facial meshes are retained.
'''
(out/'Avatar-v42-Review.md').write_text(report,encoding='utf-8')
record=json.loads((work/'resume42-baseline.json').read_text(encoding='utf-8-sig'));assert record['latest_verified_review_version']=='v41'
prior_archive=record['archive'];record.update(latest_verified_review_version='v42',updated='2026-11-19',owner='Codex',archive='artifacts/avatar-v42-codex-20261119',rollback_baseline_archive=prior_archive,status='v42 crown and fine-strand refinement verified in Blender; integrated application remains v41; browser review of the new strand material pending')
names=['zachary_character_v42_candidate.glb','Zachary_Avatar_v42_Review.blend','avatar-v42-pose-targets.json','Avatar-v42-Review.md','avatar-v42-comparison.jpg','avatar-v42-review-views.jpg','full42-front.png','full42-audit.json']
record['files']={n:{'path':record['archive']+'/outputs/'+n,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in names}
record['changes']=['Softened crown facets with bounded local relaxation: 653 hair vertex copies, maximum movement 1.801 mm.','Added 38 fine tapered round filaments along the curtain fringe and crown, with source-surface rig weight transfer and no new texture images.','Preserved all v41 facial/eye/eyelid/glasses/ear geometry, original UVs, textures, weights, expressions and lower hair boundaries.']
record['verification']=['449 preservation, geometry, manifold, winding, rig and budget checks passed; zero failed.','Fresh exported GLB rendered from five angles plus seven facial views in Blender.','Saved Blender file reopened: fourteen facial frames, six synchronized meshes, packed images and four gestures verified.','All 1256 filament vertices verified against Head transforms at three rotations; sampled raised-brow forehead clearance positive.','Project WebGL governance audit passed; v42 browser appearance/performance and application integration pending.']
record['next_work']=['Review the new filament material in application lighting and at portfolio distances; consider LOD and anti-aliasing.','Broader sculpted hair clumps and fringe outline polish.','Native Blender-baked collar/wrist atlas margins and residual skin/cloth/hand detail.']
record['application_model']['latest_candidate_integrated']=False
record['application_model']['verification_record']=prior_archive+'/outputs/Avatar-v41-Review.md'
record['active_work']='v42 adds sparse fine hair strands and softly relaxes the crown on the v41 baseline. The existing v41 face/eye improvements and application integration remain intact. New SM_Character_HairFilaments uses an opaque vertex-color material; verify its appearance under the application lighting and at distance before integration. Existing base-color UV2 and normal/parameter UV1 are unchanged.'
(work/'avatar-latest-v42.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified Blender review: **v42**, 19 November 2026, Codex.','','**v41 remains integrated in the portfolio.** v42 is a verified Blender hair-refinement candidate; browser appearance/performance and integration checks remain pending.','','## Files','']+[f'- [{n}]({record["files"][n]["path"]})' for n in names]
for title,field in [('Changes','changes'),('Verification','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+x for x in record[field]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'v41 integration evidence: '+record['application_model']['verification_record'], '']
(work/'AVATAR_LATEST-v42.md').write_text('\n'.join(lines),encoding='utf-8');print('DELIVERY_READY',len(names))
