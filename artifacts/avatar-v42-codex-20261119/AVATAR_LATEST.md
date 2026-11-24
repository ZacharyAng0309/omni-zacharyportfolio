# Latest avatar refinement status

Latest verified Blender review: **v42**, 19 November 2026, Codex.

**v41 remains integrated in the portfolio.** v42 is a verified Blender hair-refinement candidate; browser appearance/performance and integration checks remain pending.

## Files

- [zachary_character_v42_candidate.glb](artifacts/avatar-v42-codex-20261119/outputs/zachary_character_v42_candidate.glb)
- [Zachary_Avatar_v42_Review.blend](artifacts/avatar-v42-codex-20261119/outputs/Zachary_Avatar_v42_Review.blend)
- [avatar-v42-pose-targets.json](artifacts/avatar-v42-codex-20261119/outputs/avatar-v42-pose-targets.json)
- [Avatar-v42-Review.md](artifacts/avatar-v42-codex-20261119/outputs/Avatar-v42-Review.md)
- [avatar-v42-comparison.jpg](artifacts/avatar-v42-codex-20261119/outputs/avatar-v42-comparison.jpg)
- [avatar-v42-review-views.jpg](artifacts/avatar-v42-codex-20261119/outputs/avatar-v42-review-views.jpg)
- [full42-front.png](artifacts/avatar-v42-codex-20261119/outputs/full42-front.png)
- [full42-audit.json](artifacts/avatar-v42-codex-20261119/outputs/full42-audit.json)

## Changes

- Softened crown facets with bounded local relaxation: 653 hair vertex copies, maximum movement 1.801 mm.
- Added 38 fine tapered round filaments along the curtain fringe and crown, with source-surface rig weight transfer and no new texture images.
- Preserved all v41 facial/eye/eyelid/glasses/ear geometry, original UVs, textures, weights, expressions and lower hair boundaries.

## Verification

- 449 preservation, geometry, manifold, winding, rig and budget checks passed; zero failed.
- Fresh exported GLB rendered from five angles plus seven facial views in Blender.
- Saved Blender file reopened: fourteen facial frames, six synchronized meshes, packed images and four gestures verified.
- All 1256 filament vertices verified against Head transforms at three rotations; sampled raised-brow forehead clearance positive.
- Project WebGL governance audit passed; v42 browser appearance/performance and application integration pending.

## Remaining work

- Review the new filament material in application lighting and at portfolio distances; consider LOD and anti-aliasing.
- Broader sculpted hair clumps and fringe outline polish.
- Native Blender-baked collar/wrist atlas margins and residual skin/cloth/hand detail.

## Shared-workstation handoff

v42 adds sparse fine hair strands and softly relaxes the crown on the v41 baseline. The existing v41 face/eye improvements and application integration remain intact. New SM_Character_HairFilaments uses an opaque vertex-color material; verify its appearance under the application lighting and at distance before integration. Existing base-color UV2 and normal/parameter UV1 are unchanged.
v41 integration evidence: artifacts/avatar-v41-antigravity-20261119/outputs/Avatar-v41-Review.md
