# Latest avatar refinement status

Latest verified Blender review: **v40**, updated 19 November 2026 by Codex.

**v38 remains integrated in the portfolio.** v40 is the verified fringe repair candidate; browser/application checks remain pending.

## Files

- [zachary_character_v40_candidate.glb](artifacts/avatar-v40-codex-20261119/outputs/zachary_character_v40_candidate.glb)
- [Zachary_Avatar_v40_Review.blend](artifacts/avatar-v40-codex-20261119/outputs/Zachary_Avatar_v40_Review.blend)
- [avatar-v40-pose-targets.json](artifacts/avatar-v40-codex-20261119/outputs/avatar-v40-pose-targets.json)
- [Avatar-v40-Review.md](artifacts/avatar-v40-codex-20261119/outputs/Avatar-v40-Review.md)
- [avatar-v40-comparison.jpg](artifacts/avatar-v40-codex-20261119/outputs/avatar-v40-comparison.jpg)
- [avatar-v40-review-views.jpg](artifacts/avatar-v40-codex-20261119/outputs/avatar-v40-review-views.jpg)
- [full40-front.png](artifacts/avatar-v40-codex-20261119/outputs/full40-front.png)
- [full40-audit.json](artifacts/avatar-v40-codex-20261119/outputs/full40-audit.json)

## Changes

- Harmonized painted fringe colors across Face/Hair while retaining source skin and wispy edges.
- Dedicated UV repair patches occupy unused atlas areas; base color uses UV2, original UV0/UV1 retained for other maps.
- Localized surface relaxation below the part; rig, topology, active facial vertices and original morph position targets retained.

## Verification

- 1196 preservation, corner mapping, geometry, sampled UV-overlap, color and budget checks passed; zero failed.
- Fresh exported GLB matches the Blender fringe preview; five angles and seven facial review views inspected.
- Saved Blender review reopened: fourteen facial frames, six synchronized meshes, packed images and gesture targets verified.
- Current project governance audit passed; v40 application/browser integration remains pending.

## Remaining work

- Finer natural fringe strands and broader hair silhouette polish
- Eye shading, skin detail and residual surface/texture facets
- Collar/wrist atlas margins and hand/cloth detail
- v40 browser appearance and application integration with base-color UV2; release gates

## Shared-workstation handoff

v40 repairs the painted fringe color/mapping discontinuity with dedicated atlas space and restrained surface relaxation. Preserve TEXCOORD_2 for Face/Hair base color and UV1 for hair normal/parameter maps. The six-mesh schema-v4 facial contract is unchanged. v38 remains integrated; v40 is a verified Blender review candidate pending browser checks.
Prior application integration records and immutable review archives are preserved. GLB contains rig/morph data; review keyframes are in Blender.
