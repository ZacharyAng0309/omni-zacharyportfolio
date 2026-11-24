# Latest avatar refinement status

Latest verified review: **v33**, updated 12 November 2026 by Codex.

Archive: `artifacts/avatar-v33-codex-20261112`. Whole-model refinement remains in progress; not a production release.

## Latest files

- [zachary_character_v33_candidate.glb](artifacts/avatar-v33-codex-20261112/outputs/zachary_character_v33_candidate.glb)
- [Zachary_Avatar_v33_Review.blend](artifacts/avatar-v33-codex-20261112/outputs/Zachary_Avatar_v33_Review.blend)
- [avatar-v33-pose-targets.json](artifacts/avatar-v33-codex-20261112/outputs/avatar-v33-pose-targets.json)
- [Review, verification and limitations](artifacts/avatar-v33-codex-20261112/outputs/Avatar-v33-Review.md)
- [Blender expression review](artifacts/avatar-v33-codex-20261112/outputs/avatar-v33-mouth-review.jpg)
- [Oral geometry cutaway](artifacts/avatar-v33-codex-20261112/outputs/avatar-v33-oral-cutaway.png)

## Changes

- Added approximate upper/lower dental crowns and a tongue using Blender geometry, with no new textures.
- Lower teeth and tongue follow the opening/jaw/AA shapes; the tongue clears the dental arch in reviewed poses.
- Preserved every existing v32 mesh, material, texture and accessor; new anatomy remains hidden in the neutral front review.

## Verified evidence

- 238 preservation, data, topology, weight, clearance and intersection checks passed; zero failures.
- Fresh exported GLB reviewed in Blender across ten expressions plus three-quarter and side speech views.
- Saved Blender file reopened: five facial meshes synchronized; all imported morph vertices, packed textures and gesture positions verified.
- Project WebGL governance audit passed with zero violations; v33 candidate budgets checked separately.

## Remaining work

- Improve eyelid structure and soft eye/lip texture
- Refine lip/cheek motion and simplified oral anatomy
- Refine independent finger creasing and fingertip detail
- Raised-elbow cloth, remaining station poses, website integration and release gates

## Shared-workstation handoff

v33 oral detail and clearance checks verified. Next focus: eyelid structure and facial texture. Synchronize all five facial meshes during application integration.
The teeth and tongue are artistic approximations; no personal open-mouth reference was available. Individual dental anatomy, gums and palate remain simplified.
Drive matching target names on SM_Character_Face, SM_Character_OralCavity, SM_Character_UpperTeeth, SM_Character_LowerTeeth and SM_Character_Tongue. Upper-teeth targets intentionally contain zero deltas. Reset inactive values on all meshes.
The schema-version-3 pose JSON lists all five meshes. Existing arm targets and cached-rest-quaternion multiplied by local-X finger curl remain applicable, with thumb multiplier 0.55.
The public portfolio model is unchanged. Browser interpolation, application tests/build and VaultLinter release gates remain pending. The governance pass covers current project source/public assets, with separate numeric checks for the candidate.
The GLB contains rig and morph data. Facial and gesture review keyframes are stored in the Blender file.
Preserve earlier archives. Update this record after each exported, Blender-verified and archived candidate.
