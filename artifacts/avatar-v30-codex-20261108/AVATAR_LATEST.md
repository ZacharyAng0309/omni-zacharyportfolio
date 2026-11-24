# Latest avatar refinement status

Latest verified review: **v30**, updated 8 November 2026 by Codex.

Archive: `artifacts/avatar-v30-codex-20261108`. Whole-model refinement remains in progress; this is not a production release.

## Latest files

- [zachary_character_v30_candidate.glb](artifacts/avatar-v30-codex-20261108/outputs/zachary_character_v30_candidate.glb)
- [Zachary_Avatar_v30_Review.blend](artifacts/avatar-v30-codex-20261108/outputs/Zachary_Avatar_v30_Review.blend)
- [avatar-v30-pose-targets.json](artifacts/avatar-v30-codex-20261108/outputs/avatar-v30-pose-targets.json)
- [Review, verification and limitations](artifacts/avatar-v30-codex-20261108/outputs/Avatar-v30-Review.md)
- [Blender comparison](artifacts/avatar-v30-codex-20261108/outputs/avatar-v30-finger-web-comparison.jpg)

## Changes

- Removed erroneous bridges between middle and ring fingers on both hands, retaining their palm connections.
- Transferred UVs and weights to appended cut-surface vertices; retained original vertex indices and attributes.
- Cleaned Boolean slivers and verified original cuff boundaries with no additional open or non-manifold edges.

## Verified evidence

- 94 preservation, topology, gap-clearance, UV/weight and size checks passed, zero failures.
- All 2,078 active hand vertices agree with Blender skinning within 0.001 mm in six poses.
- Both hands reviewed with uniform and independent finger curls; full-body views and gestures rendered.
- Final Blender file reopened; six hand-review frames, whole-body gestures and packed images verified.

## Remaining work

- Facial detail and likeness review against the local portrait
- Coarse cut rims/fingertips and independent-finger creasing
- Raised-elbow garment deformation
- Remaining station poses, website integration and release gates

## Shared-workstation handoff

v30 finger-web repair verified; next focus is facial detail and likeness, with finer hand articulation still pending.
The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.
Finger animation remains rest-quaternion × local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.
The GLB has the rig and weights; the Blender file has keyed review demonstrations. The pose JSON supplies the application contract.
The hand review includes independent middle/ring curls at frames 161 and 201. Creasing remains visible in those stress tests.
Preserve earlier version directories. Update this record after each exported, Blender-verified and archived candidate.
