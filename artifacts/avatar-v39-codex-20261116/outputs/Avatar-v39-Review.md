# Avatar v39 — side/rear hair and shading-seam cleanup

16 November 2026. **NO-SHIP:** Blender-verified review candidate. v38 remains the integrated application model.

## Changes retained

This pass follows the v38 hair refinement and the subsequent application integration recorded in the shared handoff. The supplied frontal portrait remains the likeness reference. Side/back shape is inferred; no independent likeness score is claimed.

- Local Laplacian relaxation moves 911 existing side/rear hair vertex copies by at most 1.600 mm. The edit is bounded away from the frontal fringe and crown part, with every mesh boundary pinned. Triangle orientation and area are preserved. Some rear surface irregularity remains.
- Reconciled coincident UV-split normals in 252 compatible face/eyelid groups. 534 Face and 4 Eyelids base normal copies changed. Groups use a 1 micrometre position tolerance and only combine vertices whose eight position targets remain coincident. Existing eyelid normal targets are adjusted consistently. This brings part of the runtime shading repair into the portable asset; it does not change face geometry or texture.
- Blender comparisons show less angular lip shading and modestly smoother side/back hair. The painted hairline and some cheek texture facets are still visible. The original seven embedded image payloads, all UVs, materials, topology, skin weights, joint transforms and all morph POSITION deltas remain byte-preserved.

Two trial previews added six tapered fringe locks. They looked like overlapping pieces and introduced visible shading/coverage artifacts. Those overlays and their new texture/material are **excluded** from the final candidate. The frontal fringe geometry is unchanged; this pass does not claim to have fixed its painted edge.

## Verification scope

- **2,588 checks passed, zero failed.** Scope: data preservation and finiteness, all seven original images, hair movement/boundary/triangle constraints, all 135 face/hair seam pairs, 252 repaired shading groups at rest and across eight target values, and resource budgets. This count includes repeated per-group normal continuity assertions, not independent visual judgments.
- Fresh exported GLB imported and rendered in Blender 5.2.2 from front, quarter, side, top and back. Facial review renders cover neutral, smile, speech, asymmetric speech, blink with raised brows, and quarter/side speech. Fourteen facial review keyframes remain available.
- Saved Blender review reopened: fourteen facial frames, six synchronized morph meshes, imported position-target values and packed images verified. Four gesture poses checked numerically on 198 sampled vertices each, below 0.001 mm difference. Prior eye visibility checks were not repeated because eye/lid positions, eye geometry and all position targets are unchanged.
- **Budgets:** 44,910 triangles; 2,551,464 bytes; 52 joints; seven images, each below 100 KB. No additional mesh, texture, material, bone or morph channel is delivered.
- Current project WebGL governance audit passed with zero violations; candidate budgets checked separately. The v39 candidate has not been integrated or browser-tested. No application tests/build or VaultLinter release gate was rerun for this Blender-only pass.

The initial attempt was blocked by an approval-service usage limit. On 16 November the approved Blender run succeeded. The live add-on remained unavailable; installed Blender background rendering and saved-file inspection provided verification. No user assistance is needed for the saved review.

## QA verdict and next work

**NO-SHIP.** Remaining issues: the forehead/fringe texture transition, loose silhouette strands, coarse rear hair form, eye shading, facial texture fidelity, collar/wrist atlas margins and hand/cloth detail. The fringe requires an authored hairline/texture repair or a more complete groom; adding a few overlay locks was not sufficient.

The shared handoff reports v38 integrated and browser-verified with six-mesh facial synchronization, hair lighting adjustments, finger/rest-quaternion repairs and updated poses. The public v38 model is preserved (SHA-256 `ec703d9fe5ffd3f7af1109eef6e979fe5e50e1f72aff72ce4b6dcf357280f4a3`). Its prior integration record is retained in `work/resume39-baseline.json` in the v39 archive. v39 keeps the same schema-v4 six-mesh contract and adds no runtime requirements. Browser appearance must still be checked before substituting v39 in the app, particularly with its existing normal-welding and material overrides.

The GLB contains model/rig/morph data; Blender contains the review poses. v38 remains the rollback baseline. Application source and public model were not changed by this pass.
