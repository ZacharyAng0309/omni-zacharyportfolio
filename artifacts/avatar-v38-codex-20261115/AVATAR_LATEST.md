# Latest avatar refinement status

Latest verified review: **v38**, updated 15 November 2026 by Codex.

Whole-model refinement remains in progress; not a production release.

## Files

- [zachary_character_v38_candidate.glb](artifacts/avatar-v38-codex-20261115/outputs/zachary_character_v38_candidate.glb)
- [Zachary_Avatar_v38_Review.blend](artifacts/avatar-v38-codex-20261115/outputs/Zachary_Avatar_v38_Review.blend)
- [avatar-v38-pose-targets.json](artifacts/avatar-v38-codex-20261115/outputs/avatar-v38-pose-targets.json)
- [Avatar-v38-Review.md](artifacts/avatar-v38-codex-20261115/outputs/Avatar-v38-Review.md)
- [avatar-v38-comparison.jpg](artifacts/avatar-v38-codex-20261115/outputs/avatar-v38-comparison.jpg)
- [avatar-v38-hair-views.jpg](artifacts/avatar-v38-codex-20261115/outputs/avatar-v38-hair-views.jpg)
- [full38-front.png](artifacts/avatar-v38-codex-20261115/outputs/full38-front.png)
- [full38-audit.json](artifacts/avatar-v38-codex-20261115/outputs/full38-audit.json)

## Changes

- Soft crown-part dip, maximum 5.448 mm; 130 existing hair vertices adjusted.
- Directional brown strand groups with newly baked albedo, normal and roughness/specular maps.
- All shared hair/face boundaries, topology, weights, facial targets and unrelated materials preserved.

## Verification

- 337 geometry, preservation and budget checks passed; zero failed.
- Fresh GLB rendered from five hair angles and during facial motion; saved Blender review reopened.
- Fourteen facial frames, six synchronized meshes, packed textures and four gesture targets verified.
- Current project governance audit passed; application integration and release gates remain pending.

## Remaining work

- Fringe edge cleanup, loose silhouette strands and less uniform strand flow
- Side/back hair surface refinement; one frontal reference limits likeness
- Eye shading, face texture, lip/cheek motion and hand/cloth detail
- Six-mesh application integration, browser appearance and release gates

## Shared-workstation handoff

v38 crown-part and baked strand refinement verified. Hair remains a review candidate, with jagged fringe edges and side/rear lumps still visible. Continue silhouette/fringe cleanup. Schema-v4 animation must synchronize all six facial meshes. Public application model unchanged.
GLB contains rig/morph data; review keyframes are in Blender. Preserve prior immutable archives.
