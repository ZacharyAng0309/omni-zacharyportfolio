# Zachary avatar — v21 review candidate

Prepared 30 October 2026. This is a refinement candidate, not a production release.

## Restored source

The website loads `projects/ZacharyPortfolio/public/models/zachary_character.glb`. Its saved timestamp is later than `zachary_character_v20_r1.glb`. The source contains seven mesh groups, nine materials, one embedded 2048 × 2048 WebP atlas, a skeleton, and eight facial morph targets. It was restored into Blender. No portfolio .blend project was found in the searched project and vault files.

Original source SHA-256: `2f1dbea498ff7e25ab1c3cc849ccec7a2ab70bfd5bd2a28b52538e4ea7579de4`.

## Changes

- Simplified the three untextured spectacle components from 37,864 to 6,814 triangles. The glasses remain parented to the original head joint.
- Reduced excess crown height by about 13 mm with a smooth taper that leaves the lower hairline fixed. This is an interpretation of the portrait silhouette, not a new anatomical measurement.
- Applied restrained, seam-aware facial surface relaxation, limited to 0.6 mm. Kept vertex ordering, triangles, UVs and authored smooth normals.
- Removed metallic response from skin and fabric; adjusted skin, hair and clothing color factors and roughness; reduced the opaque contribution of the lenses.
- Corrected both blink targets. The old targets enlarged the apparent eye opening. The revised local vertical deformation closes the painted eye region in the checked render. This is still a scan-based facial surface, not newly built anatomical eyelids.
- Kept all joint transforms, joint order, bind matrices, skin weights and texture bytes unchanged. Kept all eight expression names; six expression targets are unchanged.

## Measured budget

| Measure | Original | v21 |
|---|---:|---:|
| Triangles | 72,933 | 41,883 |
| Glasses triangles | 37,864 | 6,814 |
| GLB bytes | 2,290,076 | 1,731,772 |
| GLB size, decimal MB | 2.29 | 1.73 |
| Facial expression targets | 8 | 8 |

Triangle count falls by 42.6%; file size falls by 24.4%. These are asset measurements, not measured browser frame-rate improvements. No texture resolution was sacrificed. The candidate is below the project's 3 MB avatar limit.

## Validation and evidence

63 asset checks passed, 0 failed. Coverage: unchanged source hash; skeleton hierarchy, bind matrices and joint order; six body mesh topologies, UVs and skinning arrays; six retained expression targets; two bounded blink corrections; valid indices, finite positions, unit normals and normalized four-influence weights; identical embedded image bytes; GLB size budget.

The exported candidate was imported back into Blender and rendered from front, three-quarter, side and full-body views. Neutral, smile and bilateral blink were rendered. The original and candidate share the same neutral studio lighting and camera for comparison. The generated `avatar-v21-comparison.jpg` shows original on the left and candidate on the right.

The workstation governance audit returned 0 violations. This is a static project check; it does not certify visual quality or browser performance. No application source was changed and no application unit suite was run for this asset-only candidate.

## QA verdict: NO-SHIP — review candidate

The asset is restored and technically lighter, but the full requested visual refinement is not complete.

**Major remaining issues:**

1. The scan texture has blurred eye detail and baked lighting. Material tuning does not restore missing photographic detail. A higher-quality face texture and controlled multi-view projection/baking are needed for a substantial likeness improvement.
2. Hair remains a textured scan shell. Its highlight patterns and clump structure still look soft from close range.
3. The neck/collar boundary remains visibly jagged at close range and needs a deliberate topology/material-boundary repair.
4. The original smile and mouth-opening targets are preserved, not certified as convincing facial animation. Anatomical eye and mouth topology remain a limitation.
5. Measured candidate height is approximately 1.745 m, versus the 1.71 m design specification. A coordinated scale correction needs to include the browser's fixed pose and staging assumptions; it was not silently applied to the shared skeleton.

**Not tested:** browser frame rate or rendering under the website's lighting; complete motion-range collision testing; anatomical eyelid/mouth quality; user likeness acceptance. The current website still uses the original model.

## Files and handoff

- `Zachary_Avatar_v21_Review.blend`: original and candidate scenes; candidate active with a neutral expression.
- `zachary_character_v21_candidate.glb`: independent candidate, not a replacement for the website model.
- `avatar-v21-comparison.jpg`: same-camera, same-lighting visual comparison.
- `avatar-v21-validation.json` and `avatar-v21-metrics.json`: checks and measured data.

The shared workstation copy lives under `projects/ZacharyPortfolio/artifacts/avatar-v21-codex-20261030/`. Original GLBs, Gemini configuration, application source and existing documentation are not overwritten.

The next substantive refinement should rebuild the eye/eyelid and collar regions and replace the blurred facial texture, using the user's portrait as the identity reference. Preserve this candidate as a rollback point and use a new version for that work.
