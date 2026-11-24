# Avatar v40 — painted fringe texture repair

Blender review completed 17 November 2026; handoff saved 19 November 2026. **NO-SHIP:** verified Blender review candidate. v38 remains the integrated application model.

## Repair

The gray/brown patches around the part crossed both Face and Hair material domains. v40 harmonizes those existing painted hair pixels with the established curtain-strand material while retaining the source skin and wispy outline. A restrained joint surface relaxation below the part moves 14 existing Face and 38 Hair vertex copies by no more than 2.001 mm. All vertices with nonzero facial position targets are protected; all 135 original Face/Hair seam pairs stay coincident.

The original forehead mapping had insufficient local texture area for a clean direct bake. A dedicated angle-based unwrap now covers 122 Face and 729 Hair triangles. It occupies proven unused 768×768 rectangles within the existing atlases: Face at pixel (896,16), Hair at (1264,400). The texture dimensions and image count do not increase. The two base-color textures now use **TEXCOORD_2**. Original UV0/UV1 remain unchanged per triangle corner, so the hair normal and roughness/specular maps continue to use UV1 correctly.

UV splits add 552 vertex copies; their positions, normals, joints, weights and all morph deltas are copied from the corresponding source vertices. Triangle count and the six-mesh facial contract are unchanged. Existing skin texture and strand outline are retained; this is a targeted color/mapping correction, not a new strand groom or a complete likeness rebuild.

## Verification scope

- **1,196 checks passed, zero failed.** Every remapped triangle corner is checked against the expected geometry, original UVs, weights and morph data. Unchanged accessors, five unchanged image payloads, node/rig data, atlas-slot occupancy, moved-triangle orientation/area, active facial-vertex preservation and budgets are checked.
- The dedicated unwrap has zero overlapping pixel-centre samples on a 512×512 audit grid. This is a finite sampled check, not an exact continuous intersection proof. The source triangle/corner mapping is verified geometrically before baking.
- Outside the remapped patch, 3,000 Face and 2,698 Hair triangle-centre samples retain their colors within compression tolerances: mean absolute channel differences 1.31/255 and 0.30/255 respectively. The textures are lossy WebP, so unchanged pixels are not claimed byte-identical.
- The exported front render matches the procedural Blender preview in the fringe review region: mean channel difference 0.76/255, 95th percentile 2/255. Front, quarter, side, top and back renders were inspected; facial renders cover neutral, smile, speech, asymmetric speech, blink with raised brows, and quarter/side speech.
- Final Blender file reopened: all fourteen facial keyframes synchronize six meshes; imported morph positions, packed images and gesture targets verified. Four gestures were checked numerically with 198 sampled vertices each, below 0.001 mm difference. Eye/lid geometry and original position targets remain unchanged.
- **Budgets:** 44,910 triangles; 2,651,584 bytes; 52 joints; seven images, each below 100 KB. Face albedo is 96,992 bytes at 4096×2048; Hair albedo is 86,876 bytes at 2048×2048. No texture-resolution increase, new mesh, bone, material or morph channel.
- Project WebGL governance audit passed with zero violations. The installed Three.js GLTFLoader assigns the declared texture coordinate channel; actual v40 browser appearance and application integration remain untested. Application tests/build and VaultLinter release gates were not rerun for this Blender-only pass.

Blender 5.2.2 background mode supplied the creation, baking and saved-file verification. The final bake completed cleanly and its PNG/UV inputs are hash-verified before embedding. No external image-generation service was used.

## Authoring notes and remaining work

The final repair excludes the broad skin-repainting trials and the earlier fringe-overlay experiments. It reduces mismatched fringe color patches; the hair still has a stylized painted outline. Finer edge strands, residual surface/texture facets, eye shading, skin fidelity, and collar/wrist atlas margins remain broader refinement work. No calibrated likeness score is claimed.

For further baking, retain the distinction between base-color UV2 and normal/parameter UV1. Refresh mesh/UV references after Blender edit-mode operations, separate the material-boundary UV seams, and explicitly pack all islands together. Those safeguards prevent stale UV writes and cross-material overlaps. Final reproduction: `fringe40-shape.py` → import with `review39.py --prepare-only` → `fringe40-paint.py` → `fringe40-patch-bake.py` → `fringe40-patch-embed.py` → `verify40.py`. The authored material scene is retained in the archive as `work/fringe40-paint.blend`.

The schema-v4 pose contract remains Face, OralCavity, UpperTeeth, LowerTeeth, Tongue and Eyelids; eye globes follow Head. The GLB contains rig/morph data and Blender contains the review keyframes. The public portfolio remains on its previously integrated v38 model; application source and public assets are unchanged by this repair. The prior integration handoff is preserved. v39 is the rollback baseline for this pass.
