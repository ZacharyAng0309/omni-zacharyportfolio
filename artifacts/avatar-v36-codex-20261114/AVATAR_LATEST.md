# Latest avatar refinement status

Latest verified review: **v36**, updated 14 November 2026 by Codex.

Whole-model refinement remains in progress; not a production release.

## Files

- [zachary_character_v36_candidate.glb](artifacts/avatar-v36-codex-20261114/outputs/zachary_character_v36_candidate.glb)
- [Zachary_Avatar_v36_Review.blend](artifacts/avatar-v36-codex-20261114/outputs/Zachary_Avatar_v36_Review.blend)
- [avatar-v36-pose-targets.json](artifacts/avatar-v36-codex-20261114/outputs/avatar-v36-pose-targets.json)
- [Avatar-v36-Review.md](artifacts/avatar-v36-codex-20261114/outputs/Avatar-v36-Review.md)
- [avatar-v36-comparison.jpg](artifacts/avatar-v36-codex-20261114/outputs/avatar-v36-comparison.jpg)
- [avatar-v36-expressions.jpg](artifacts/avatar-v36-codex-20261114/outputs/avatar-v36-expressions.jpg)
- [full36-front.png](artifacts/avatar-v36-codex-20261114/outputs/full36-front.png)
- [full36-audit.json](artifacts/avatar-v36-codex-20261114/outputs/full36-audit.json)

## Changes

- Added real eye openings, four fitted lid loops per eye, and two separate closed eye globes.
- Added outer-lid depth motion and verified closed-lid contact with raised brows.
- Preserved source rest geometry, textures and non-blink targets; new six-mesh facial synchronization contract.

## Verification

- 1177 data, seam, topology, deformation, sampled visibility and budget checks passed; zero failed.
- Fresh exported GLB rendered across fourteen expressions and two speech angles; saved Blender review reopened successfully.
- All six facial meshes, imported morph values, packed textures and gesture targets verified.
- Current project governance audit passed with zero violations; release gates remain pending.

## Remaining work

- Refine iris/cornea appearance, iris proportions and upper-lid folds against the portrait
- Sharper face texture, lip/cheek motion and oral anatomy
- Finger creasing and raised-elbow cloth
- Six-mesh application integration, gaze controls, remaining poses and release gates

## Shared-workstation handoff

v36 structural eye/eyelid upgrade verified. Next focus: eye appearance and upper-lid likeness. IMPORTANT: schema-v4 facial animation must synchronize Eyelids along with the existing five meshes. The globes currently follow Head only.
The public portfolio model is unchanged. Application/browser and release checks remain pending. The GLB contains rig/morph data; review keyframes are in the Blender file. Preserve prior immutable archives.
