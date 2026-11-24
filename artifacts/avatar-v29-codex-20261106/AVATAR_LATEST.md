# Latest avatar refinement status

Latest verified review: **v29**, updated 6 November 2026 by Codex.

Archive: `artifacts/avatar-v29-codex-20261106`. Whole-model refinement remains in progress; this is not a production release.

## Latest files

- [zachary_character_v29_candidate.glb](artifacts/avatar-v29-codex-20261106/outputs/zachary_character_v29_candidate.glb)
- [Zachary_Avatar_v29_Review.blend](artifacts/avatar-v29-codex-20261106/outputs/Zachary_Avatar_v29_Review.blend)
- [avatar-v29-pose-targets.json](artifacts/avatar-v29-codex-20261106/outputs/avatar-v29-pose-targets.json)
- [Review, verification and limitations](artifacts/avatar-v29-codex-20261106/outputs/Avatar-v29-Review.md)
- [Blender comparison](artifacts/avatar-v29-codex-20261106/outputs/avatar-v29-palm-comparison.jpg)

## Changes

- Reduced the triangular palm dent with local surface relaxation, capped at 1.5 mm.
- Smoothed proximal hand weight transitions and refreshed normals on the edited patch.
- Preserved all 101 cuff seam vertices, topology, UVs, textures, facial morphs and v28 joint transforms.

## Verified evidence

- 83 asset-preservation, cuff, normal/weight, triangle-validity and size checks passed, zero failures.
- Exported GLB reviewed in Blender across four curls, both hands, full-body views and three gestures.
- Moderate/strong-curl 99th-percentile edge ratios improved from 1.188/1.373 to 1.151/1.277.
- Saved Blender review reopened; whole-model gestures, finger animation and packed images verified.

## Remaining work

- Repair fused middle/ring finger web and improve coarse fingertip anatomy
- Facial detail and likeness
- Raised-elbow garment deformation
- Remaining station poses, website integration and release gates

## Shared-workstation handoff

v29 palm refinement verified; next is a localized topology repair of the fused finger web.
The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.
The v28/v29 finger animation convention is rest-quaternion × local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.
The GLB has the rig and weights; the Blender file has keyed review demonstrations. The pose JSON supplies the application contract.
Preserve earlier version directories. Update this record after each exported, Blender-verified and archived candidate.
