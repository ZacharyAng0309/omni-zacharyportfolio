# Avatar v37 — eye placement, iris and lid tuning

15 November 2026. **NO-SHIP:** Blender-verified review candidate; likeness and website integration remain unfinished.

## Change and reference assessment

The supplied frontal portrait was inspected beside v36, including a magnified eye crop. v36 had a relatively flat horizontal opening, large dark pupil and high eye line within the frames. v37 tests a lower assembly, a fuller visible iris and a restrained corner angle. These are artist-guided adjustments from a single photo, not calibrated biometric measurements or a verified likeness score.

- Lowered the eyes by 1.6 mm with proportional support in the surrounding face and a small fringe region. This changes Y positions only on Face/Hair. All 135 original hair/face seam pairs remain coincident.
- Changed pupil radius from 2.5 to 2.0 mm and iris radius from 5.3 to 5.8 mm. The globe's outer silhouette is retained. Warm brown vertex colors replace the previous iris colors; no texture was generated or repainted.
- Added up to 0.8 mm lateral widening and a modest outer-corner lift to the inner lid loops, with a fuller lower arc and a 0.2 mm upper-lid crease. The neutral lid fit changes while its previous closed endpoint is preserved before translating the eye assembly.
- Reduced the eye material's broad reflection (specular factor 0.20 to 0.10, roughness 0.23 to 0.14). Front and quarter renders show a lower eye line and less of the thin horizontal slit from v36. The result remains stylized.

The edit preserves topology, UVs, seven embedded image payloads, skin weights, node transforms and the six-part facial target contract. All original Face morph deltas are preserved; eyelid blink POSITION targets and eyelid NORMAL targets are updated for the revised neutral shape. Unrelated materials and meshes remain unchanged, including the active oral surface. The eye-support displacement also affects 51 hair vertex copies; this is documented rather than treated as an eyes-only buffer edit.

## Verification scope

- **1226 checks passed, zero failed.** Scope: preserved accessors, textures, scene structure, weights, local placement bounds, face/hair seams, active oral vertices, and all eight target values at each original eyelid/face boundary point.
- **Ten numeric eye cases:** neutral, quarter/half/three-quarter/full blink, blink with raised brows, both winks, raised brows and speech. No sampled globe point protrudes through skin outside the intended opening. Full blink and blink+brow hide every sampled globe point. Finite ray samples are not an exhaustive continuous intersection proof.
- Eyelid front orientation and nonzero triangle area remain valid in checked cases. The two globes retain closed topology. Face + Eyelids + OralCavity retain the same edge multiplicities as v36, including the two intended eye apertures; the whole character is not claimed watertight.
- Fresh GLB imported and rendered in Blender: fourteen expressions, quarter/side speech, portrait front/quarter and full body. Four gesture poses checked numerically. The saved Blender file was reopened: fourteen facial frames synchronize six meshes; imported morph vertices, packed images and gesture wrist targets verified.
- **Budgets:** 44,910 triangles; 2,547,892 bytes; 52 joints. Seven image payloads, each below 100 KB. No added polygons or textures.
- Current project WebGL governance audit passed with zero violations. It covers current project source/public assets; candidate budgets were checked separately. Application/browser integration, tests/build and VaultLinter release gates remain pending.

Blender 5.2.2 ran in the background; the live add-on connection was unavailable. No external generation service was used, and no assistance was required to complete this pass.

## Remaining work and integration

The iris/cornea shading and lid transitions still look simplified. Subtle asymmetry, tear ducts and more faithful skin detail remain open likeness work. No independent gaze rig exists. A single frontal image limits accurate side/back reconstruction. Lip/cheek motion, oral detail, finger creasing and raised-elbow cloth also remain unfinished.

The schema-version-4 pose file still requires matching target values on **Face, OralCavity, UpperTeeth, LowerTeeth, Tongue and Eyelids**, resetting inactive values on all six each frame. EyeLeft/EyeRight follow Head without morph targets. Updating only the old five facial meshes breaks blink closure.

`Zachary_Avatar_v37_Review.blend` contains portrait, full-body gesture and facial-expression scenes; facial markers span frames 1–521. The GLB contains mesh, rig and morph data; review keyframes are stored in Blender. The public portfolio model and application source are unchanged. Preserve v36 as the rollback baseline.
