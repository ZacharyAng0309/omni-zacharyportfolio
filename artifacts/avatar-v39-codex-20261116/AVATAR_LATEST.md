# Latest avatar refinement status

Latest verified Blender review: **v39**, updated 16 November 2026 by Codex.

**v38 remains integrated in the portfolio.** v39 is a Blender review candidate pending browser/application verification.

## Files

- [zachary_character_v39_candidate.glb](artifacts/avatar-v39-codex-20261116/outputs/zachary_character_v39_candidate.glb)
- [Zachary_Avatar_v39_Review.blend](artifacts/avatar-v39-codex-20261116/outputs/Zachary_Avatar_v39_Review.blend)
- [avatar-v39-pose-targets.json](artifacts/avatar-v39-codex-20261116/outputs/avatar-v39-pose-targets.json)
- [Avatar-v39-Review.md](artifacts/avatar-v39-codex-20261116/outputs/Avatar-v39-Review.md)
- [avatar-v39-comparison.jpg](artifacts/avatar-v39-codex-20261116/outputs/avatar-v39-comparison.jpg)
- [avatar-v39-review-views.jpg](artifacts/avatar-v39-codex-20261116/outputs/avatar-v39-review-views.jpg)
- [full39-front.png](artifacts/avatar-v39-codex-20261116/outputs/full39-front.png)
- [full39-audit.json](artifacts/avatar-v39-codex-20261116/outputs/full39-audit.json)

## Changes

- Bounded side/rear hair relaxation, maximum 1.601 mm; frontal fringe, crown part and boundaries retained.
- 252 compatible face/eyelid shading groups reconciled; less angular lip shading.
- All topology, seven image payloads, UVs, weights and morph position deltas preserved; experimental fringe overlays excluded.

## Verification

- 2588 preservation, geometry, shading-continuity and budget checks passed; zero failed.
- Fresh GLB rendered at five angles and through seven facial review views; saved Blender review reopened.
- Fourteen facial frames, six synchronized meshes, packed images and four gesture targets verified.
- Current project governance audit passed; v39 application integration/browser checks pending.

## Remaining work

- Fringe edge cleanup, loose silhouette strands and less uniform strand flow
- Side/back hair surface refinement; one frontal reference limits likeness
- Eye shading, face/body texture bake (T_Face_v34_Albedo top hairline bleed and hoodie collar/wrist UV dilation >= 16px), lip/cheek motion and hand/cloth detail

## Shared-workstation handoff

v39 Blender review verifies side/rear hair relaxation and face/eyelid UV-split normal repair. Fringe overlay trials were rejected. Continue authored forehead/hairline texture repair and hair silhouette work. v38 remains integrated and browser-verified per the preserved application handoff; v39 is not integrated.
Prior v38 integration and runtime changes are preserved in [application handoff](artifacts/avatar-v39-codex-20261116/work/resume39-baseline.json). GLB contains rig/morph data; review keyframes are in Blender. Preserve prior immutable archives.
