# Latest avatar refinement status

Latest verified review: **v28**, updated 4 November 2026 by Codex.

Archive: `artifacts/avatar-v28-codex-20261104`. Whole-model refinement remains in progress; this is not a production release.

## Latest files

- [zachary_character_v28_candidate.glb](artifacts/avatar-v28-codex-20261104/outputs/zachary_character_v28_candidate.glb)
- [Zachary_Avatar_v28_Review.blend](artifacts/avatar-v28-codex-20261104/outputs/Zachary_Avatar_v28_Review.blend)
- [avatar-v28-pose-targets.json](artifacts/avatar-v28-codex-20261104/outputs/avatar-v28-pose-targets.json)
- [Review, verification and limitations](artifacts/avatar-v28-codex-20261104/outputs/Avatar-v28-Review.md)
- [Blender comparison](artifacts/avatar-v28-codex-20261104/outputs/avatar-v28-finger-comparison.jpg)

## Changes

- Fitted all 30 finger pivots to hand surface midlines and corrected palmward bend axes.
- Rebuilt hand weights with bone envelopes and a smooth geodesic cuff blend; preserved all 101 cuff seam vertices.
- Retained v27 arm targets and specified rest-relative quaternion finger curl for future application integration.

## Verified evidence

- 82 structural/rest-surface/cuff/weight checks passed, zero failures.
- Exported GLBs reviewed in Blender at four curl amounts, both hands, whole-body views and three gestures.
- Moderate-curl 99th-percentile edge stretch reduced from 1.946x to 1.188x.
- Saved Blender file reopened; gesture and finger animation plus packed textures verified.

## Remaining work

- Fused finger webs, coarse tips and palm pinching
- Facial detail and likeness
- Raised-elbow garment deformation
- Remaining station poses, website integration and release gates

## Shared-workstation handoff

v28 review complete; next refinement is hand surface geometry and palm pinching.
The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.
v28 finger animation requires rest-quaternion × local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.
The GLB has the rig and weights; the Blender file has keyed review demonstrations. The pose JSON supplies the application contract.
Preserve earlier version directories. Update this record only after a new candidate is exported, checked in Blender and archived.
