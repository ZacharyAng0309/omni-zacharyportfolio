# Avatar v35 — brow and fringe surface cleanup

13 November 2026. **NO-SHIP:** verified review candidate; whole-model likeness refinement remains in progress.

## Change and observed result

This is a subtle local surface cleanup, not a new anatomical eye model. A constrained Laplacian pass relaxes the forehead/brow-to-fringe transition, with updated surface normals. Front and quarter clay renders and textured portraits were inspected in Blender. The change is small at normal portrait size; the soft source textures and simplified eyes remain clearly visible limitations.

The edit moves 164 face vertex copies and 271 hair vertex copies by at most 0.901 mm (including float rounding). The two surfaces are relaxed together so all 135 original shared seam pairs remain exactly coincident. Bounding-box extrema are fixed. The ear region, lower face, glasses, clothes, hands, skin weights, topology, UVs, materials, all six embedded texture payloads and every morph delta remain unchanged. Every face vertex participating in blinking keeps its original rest position.

## Verification scope

- **319 checks passed, zero failed:** unchanged accessors and scene structure, texture payload preservation and budgets, finite data, unit normals, bounded/localized displacement, original hair/face seams, combined edge multiplicities, and active oral-surface preservation.
- **Fourteen numeric deformation cases** checked for the modified face and hair: neutral, all eight individual targets, blink+brow, half-blink, speech, smile/speech and wide mouth. No new orientation reversals or triangles collapsing below half their baseline area. The v34 repaired eye patches also retain positive front-facing orientation in the relevant stress cases.
- **Fresh Blender renders:** front and quarter portraits; front and quarter clay comparisons; neutral, blink, half blink, left wink, right wink, blink+brow, and quarter/side speech. The full body was rendered and four gesture poses were checked numerically.
- **Saved Blender file reopened:** all 14 expression timeline frames synchronize all five facial meshes; every imported morph vertex is checked against the GLB; 12 image datablocks are packed. Gesture wrist errors remain below 0.001 mm.
- **Budgets:** 43,498 triangles, 2,354,404 bytes, 52 joints, all six textures below 100 KB. No polygon or texture budget increase from v34.
- Current project WebGL governance audit passed with zero violations. This audit covers current project source/public assets; candidate budgets were checked separately. Application tests/build, browser integration and VaultLinter release gates are pending.

Blender 5.2.2 ran in the background because the live add-on connection was unavailable. No assistance was required to complete these checks. No external generation service was used.

## Remaining work

Anatomical eyelid loops and separate eye anatomy remain the main improvement needed in this area. Further small smoothing passes will have diminishing visual benefit. Sharper facial texture, a cleaner fringe transition, lip/cheek motion, finger creasing and raised-elbow cloth also remain open. A frontal reference alone does not establish accurate side/back likeness. This version does not claim photorealism or final portfolio readiness.

## Review files and integration

`Zachary_Avatar_v35_Review.blend` includes portrait, whole-model gesture and facial-expression scenes. Facial markers run from frame 1 to 521. `zachary_character_v35_candidate.glb` contains the mesh, rig and morph data. `avatar-v35-pose-targets.json` retains the schema-version-3 contract for five synchronized facial meshes. The GLB does not contain the review timeline animation.

Drive matching targets on Face, OralCavity, UpperTeeth, LowerTeeth and Tongue; reset inactive values on all five. Existing arm targets and the cached rest quaternion multiplied by local-X finger curl remain applicable. Preserve the v34 archive. The public portfolio model and application source have not been replaced.
