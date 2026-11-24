from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
root=Path(__file__).resolve().parents[1];work=root/'work';out=root/'outputs';v=json.loads((work/'fringe40-validation.json').read_text());bv=json.loads((work/'blend40-validation.json').read_text());tx=json.loads((work/'fringe40-textures.json').read_text());rc=json.loads((work/'fringe40-render-comparison.json').read_text());assert v['checks_failed']==0 and bv['morph_meshes_synchronized']==6
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
canvas=Image.new('RGB',(1080,590),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,file) in enumerate([('Previous fringe — v39','portrait39-front.png'),('Fringe texture repair — v40','portrait40-front.png')]):
 canvas.paste(Image.open(work/file).convert('RGB').resize((540,540),Image.Resampling.LANCZOS),(i*540,50));draw.text((i*540+16,12),label,font=font,fill='white')
canvas.save(out/'avatar-v40-comparison.jpg',quality=94)
canvas=Image.new('RGB',(1080,810),(35,35,35));draw=ImageDraw.Draw(canvas)
for i,(label,file) in enumerate([('Front','portrait40-front.png'),('Quarter','portrait40-quarter.png'),('Side','portrait40-left.png'),('Smile','expression40-smile.png'),('Blink + raised brow','expression40-blink-brow.png'),('Speech','expression40-speech-quarter.png')]):
 x=i%3*360;y=i//3*405;im=Image.open(work/file).convert('RGB');im.thumbnail((360,360),Image.Resampling.LANCZOS);canvas.paste(im,(x+(360-im.width)//2,y+45));draw.text((x+12,y+10),label,font=font,fill='white')
canvas.save(out/'avatar-v40-review-views.jpg',quality=93)
report=f'''# Avatar v40 — painted fringe texture repair

Blender review completed 17 November 2026; handoff saved 19 November 2026. **NO-SHIP:** verified Blender review candidate. v38 remains the integrated application model.

## Repair

The gray/brown patches around the part crossed both Face and Hair material domains. v40 harmonizes those existing painted hair pixels with the established curtain-strand material while retaining the source skin and wispy outline. A restrained joint surface relaxation below the part moves 14 existing Face and 38 Hair vertex copies by no more than 2.001 mm. All vertices with nonzero facial position targets are protected; all 135 original Face/Hair seam pairs stay coincident.

The original forehead mapping had insufficient local texture area for a clean direct bake. A dedicated angle-based unwrap now covers 122 Face and 729 Hair triangles. It occupies proven unused 768×768 rectangles within the existing atlases: Face at pixel (896,16), Hair at (1264,400). The texture dimensions and image count do not increase. The two base-color textures now use **TEXCOORD_2**. Original UV0/UV1 remain unchanged per triangle corner, so the hair normal and roughness/specular maps continue to use UV1 correctly.

UV splits add {v['metrics']['new_uv_vertex_copies']} vertex copies; their positions, normals, joints, weights and all morph deltas are copied from the corresponding source vertices. Triangle count and the six-mesh facial contract are unchanged. Existing skin texture and strand outline are retained; this is a targeted color/mapping correction, not a new strand groom or a complete likeness rebuild.

## Verification scope

- **{v['checks_passed']:,} checks passed, zero failed.** Every remapped triangle corner is checked against the expected geometry, original UVs, weights and morph data. Unchanged accessors, five unchanged image payloads, node/rig data, atlas-slot occupancy, moved-triangle orientation/area, active facial-vertex preservation and budgets are checked.
- The dedicated unwrap has zero overlapping pixel-centre samples on a 512×512 audit grid. This is a finite sampled check, not an exact continuous intersection proof. The source triangle/corner mapping is verified geometrically before baking.
- Outside the remapped patch, 3,000 Face and 2,698 Hair triangle-centre samples retain their colors within compression tolerances: mean absolute channel differences {v['metrics']['face_unchanged_surface_color_error_255']['mean']:.2f}/255 and {v['metrics']['hair_unchanged_surface_color_error_255']['mean']:.2f}/255 respectively. The textures are lossy WebP, so unchanged pixels are not claimed byte-identical.
- The exported front render matches the procedural Blender preview in the fringe review region: mean channel difference {rc['fringe_render_mean_channel_difference_255']:.2f}/255, 95th percentile {rc['fringe_render_p95_channel_difference_255']:.0f}/255. Front, quarter, side, top and back renders were inspected; facial renders cover neutral, smile, speech, asymmetric speech, blink with raised brows, and quarter/side speech.
- Final Blender file reopened: all fourteen facial keyframes synchronize six meshes; imported morph positions, packed images and gesture targets verified. Four gestures were checked numerically with 198 sampled vertices each, below 0.001 mm difference. Eye/lid geometry and original position targets remain unchanged.
- **Budgets:** {v['metrics']['triangles']:,} triangles; {v['metrics']['glb_bytes']:,} bytes; 52 joints; seven images, each below 100 KB. Face albedo is {tx['face']['bytes']:,} bytes at 4096×2048; Hair albedo is {tx['hair']['bytes']:,} bytes at 2048×2048. No texture-resolution increase, new mesh, bone, material or morph channel.
- Project WebGL governance audit passed with zero violations. The installed Three.js GLTFLoader assigns the declared texture coordinate channel; actual v40 browser appearance and application integration remain untested. Application tests/build and VaultLinter release gates were not rerun for this Blender-only pass.

Blender 5.2.2 background mode supplied the creation, baking and saved-file verification. The final bake completed cleanly and its PNG/UV inputs are hash-verified before embedding. No external image-generation service was used.

## Authoring notes and remaining work

The final repair excludes the broad skin-repainting trials and the earlier fringe-overlay experiments. It reduces mismatched fringe color patches; the hair still has a stylized painted outline. Finer edge strands, residual surface/texture facets, eye shading, skin fidelity, and collar/wrist atlas margins remain broader refinement work. No calibrated likeness score is claimed.

For further baking, retain the distinction between base-color UV2 and normal/parameter UV1. Refresh mesh/UV references after Blender edit-mode operations, separate the material-boundary UV seams, and explicitly pack all islands together. Those safeguards prevent stale UV writes and cross-material overlaps. Final reproduction: `fringe40-shape.py` → import with `review39.py --prepare-only` → `fringe40-paint.py` → `fringe40-patch-bake.py` → `fringe40-patch-embed.py` → `verify40.py`. The authored material scene is retained in the archive as `work/fringe40-paint.blend`.

The schema-v4 pose contract remains Face, OralCavity, UpperTeeth, LowerTeeth, Tongue and Eyelids; eye globes follow Head. The GLB contains rig/morph data and Blender contains the review keyframes. The public portfolio remains on its previously integrated v38 model; application source and public assets are unchanged by this repair. The prior integration handoff is preserved. v39 is the rollback baseline for this pass.
'''
(out/'Avatar-v40-Review.md').write_text(report,encoding='utf-8')
record=json.loads((work/'resume40-baseline.json').read_text(encoding='utf-8-sig'));assert record['latest_verified_review_version']=='v39'
record.update(latest_verified_review_version='v40',updated='2026-11-19',archive='artifacts/avatar-v40-codex-20261119',status='v40 fringe texture repair verified in Blender; v38 remains integrated in the application; broader likeness refinement ongoing')
names=['zachary_character_v40_candidate.glb','Zachary_Avatar_v40_Review.blend','avatar-v40-pose-targets.json','Avatar-v40-Review.md','avatar-v40-comparison.jpg','avatar-v40-review-views.jpg','full40-front.png','full40-audit.json']
record['files']={n:{'path':record['archive']+'/outputs/'+n,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in names}
record['changes']=['Harmonized painted fringe colors across Face/Hair while retaining source skin and wispy edges.','Dedicated UV repair patches occupy unused atlas areas; base color uses UV2, original UV0/UV1 retained for other maps.','Localized surface relaxation below the part; rig, topology, active facial vertices and original morph position targets retained.']
record['verification']=['1196 preservation, corner mapping, geometry, sampled UV-overlap, color and budget checks passed; zero failed.','Fresh exported GLB matches the Blender fringe preview; five angles and seven facial review views inspected.','Saved Blender review reopened: fourteen facial frames, six synchronized meshes, packed images and gesture targets verified.','Current project governance audit passed; v40 application/browser integration remains pending.']
record['next_work']=['Finer natural fringe strands and broader hair silhouette polish','Eye shading, skin detail and residual surface/texture facets','Collar/wrist atlas margins and hand/cloth detail','v40 browser appearance and application integration with base-color UV2; release gates']
record['active_work']='v40 repairs the painted fringe color/mapping discontinuity with dedicated atlas space and restrained surface relaxation. Preserve TEXCOORD_2 for Face/Hair base color and UV1 for hair normal/parameter maps. The six-mesh schema-v4 facial contract is unchanged. v38 remains integrated; v40 is a verified Blender review candidate pending browser checks.'
record['application_model']['latest_candidate_integrated']=False
(work/'avatar-latest-v40.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified Blender review: **v40**, updated 19 November 2026 by Codex.','','**v38 remains integrated in the portfolio.** v40 is the verified fringe repair candidate; browser/application checks remain pending.','','## Files','']+[f'- [{n}]({record["files"][n]["path"]})' for n in names]
for title,field in [('Changes','changes'),('Verification','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+x for x in record[field]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'Prior application integration records and immutable review archives are preserved. GLB contains rig/morph data; review keyframes are in Blender.','']
(work/'AVATAR_LATEST-v40.md').write_text('\n'.join(lines),encoding='utf-8');print('DELIVERY_READY',len(names))
