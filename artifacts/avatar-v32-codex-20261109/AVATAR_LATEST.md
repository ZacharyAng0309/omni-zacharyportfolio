# Latest avatar refinement status

Latest verified review: **v32**, updated 9 November 2026 by Codex.

Archive: `artifacts/avatar-v32-codex-20261109`. Whole-model refinement remains in progress; this is not a production release.

## Latest files

- [zachary_character_v32_candidate.glb](artifacts/avatar-v32-codex-20261109/outputs/zachary_character_v32_candidate.glb)
- [Zachary_Avatar_v32_Review.blend](artifacts/avatar-v32-codex-20261109/outputs/Zachary_Avatar_v32_Review.blend)
- [avatar-v32-pose-targets.json](artifacts/avatar-v32-codex-20261109/outputs/avatar-v32-pose-targets.json)
- [Review, verification and limitations](artifacts/avatar-v32-codex-20261109/outputs/Avatar-v32-Review.md)
- [Blender mouth review](artifacts/avatar-v32-codex-20261109/outputs/avatar-v32-mouth-review.jpg)

## Changes

- Introduced a rounded lip opening and recessed oral cavity instead of stretching a closed mouth surface.
- Revised mouthOpen, jawOpen and viseme_aa, softened lip-corner motion, and preserved lip texture seams.
- Preserved original face vertex attributes and five other expression targets; other meshes, rig and textures are unchanged.

## Verified evidence

- 147 export, preservation, weights, topology and morph-seam checks passed; zero failures.
- Fresh exported GLB reviewed in Blender across eight facial poses plus three-quarter and side speech views.
- Final Blender file reopened: both facial meshes synchronized; all imported morph vertices, packed textures and gesture positions verified.
- No new welded boundary or nonmanifold edges; pre-existing eye-area topology issues remain.

## Remaining work

- Add and refine oral anatomy, lip contour and jaw/cheek deformation
- Improve eyelid structure and soft eye/lip texture
- Refine independent finger creasing and fingertip detail
- Raised-elbow cloth, remaining station poses, website integration and release gates

## Shared-workstation handoff

v32 structural mouth repair verified; next focus is oral anatomy, eyelids and facial detail. Both facial meshes must be driven together during application integration.
The cavity has no teeth or tongue yet. Close-up lip and cheek deformation, eyelid structure and the soft face texture remain unfinished.
The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.
Drive matching target names on SM_Character_Face and SM_Character_OralCavity every frame. The existing single-face-mesh update needs adaptation.
Finger animation remains cached rest quaternion multiplied by local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.
The pose JSON is schema version 3 and adds the facial synchronization contract. The GLB has the rig and facial targets; the Blender file has keyed facial and gesture reviews.
Preserve earlier version directories. Update this record after each exported, Blender-verified and archived candidate.
