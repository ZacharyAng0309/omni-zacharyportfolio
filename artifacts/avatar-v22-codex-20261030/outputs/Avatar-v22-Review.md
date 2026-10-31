# Zachary avatar v22 — portrait-guided ear, hair and face refinement

30 October 2026. Review candidate; not a production replacement.

## Reference and interpretation

The workstation's design specification identifies `vault/01_Wiki/Projects/ZacharyPortfolio/03_Design/stitch_assets/reference_portrait.jpg` as the real-life portrait. A copy is also in `projects/ZacharyPortfolio/public/images/reference_portrait.jpg`. The portrait was used locally as the identity reference. The generated turnaround sheet was inspected for context, not used as anatomical ground truth.

Reference observations: dark brown parted hair; a softer oval lower face; rounded ear contours; fine dark round spectacles. The portrait is a frontal view. Ear depth and the rear hair shape cannot be established precisely from it.

## Changes from v21

- Shortened the lower-face region by up to 6 mm with smooth falloff and slightly broadened the lower jaw. The eye region, nose bridge and shared mesh boundary vertices remain fixed.
- Relaxed pinched ear contours using local mesh adjacency with welded UV-seam positions. Maximum ear adjustment: approximately 1.76 mm. Attachment boundaries and the upper spectacle support region are protected.
- Made a modest additional crown/silhouette adjustment, maximum approximately 6.29 mm, while pinning the face/hair boundary.
- Added separate baked hair albedo and tangent-space normal maps. Fine procedural strand variation is blended with the source hair color, with the blend fading near mesh boundaries to avoid a visibly cut-out fringe. The original texture atlas remains unchanged for the face and body.
- Baked maps: 2048 × 2048 WebP albedo, 22,188 bytes; 1024 × 1024 PNG normal map, 67,249 bytes. This is procedural surface detail, not recovered photographic strands or a newly groomed hairstyle. The normal detail is deliberately subtle.

The first hair material trial made the fringe look too sharply cut against the forehead and was rejected. The saved candidate uses the feathered material.

## Budget and validation

Candidate GLB: **1,821,552 bytes / 1.82 MB**, below the 3 MB avatar limit. Triangles remain **41,883**. No additional mesh objects, joints, or expression targets were introduced. All eight v21 expressions, including its corrected blink shapes, remain available.

63 asset checks passed, 0 failed. Coverage: v21 source hash; skeleton hierarchy, joint ordering and bind matrices; body topology, skin weights and UVs; expression preservation/bounds; valid geometry indices, finite positions and unit normals; unchanged source image bytes; GLB budget. The workstation WebGL governance audit returned 0 violations.

The exported GLB was reimported into Blender for front, three-quarter, side, top, close ear and blink renders. This verifies the portable artifact rather than only the authoring shader. Shared face boundary displacement is 0 mm. The Blender review includes packed textures, v21, the v22 authoring material and the reimported v22 candidate.

## Visual verdict: review required; not production-certified

The face and ear revisions are restrained likeness interpretations. Their acceptance belongs to the user. Close inspection still reveals source-scan limitations: blurred eyes and skin detail, coarse hair clumps, faceted ear shading and simplified inner-ear structure, a visibly jagged neck/collar boundary, and limited anatomical eyelid/mouth topology. The ear contours were relaxed, not anatomically rebuilt. The added hair detail does not reconstruct missing high-resolution photo information.

Not tested: final website lighting or frame-rate performance, all rig poses and collision combinations, or a full facial-animation acceptance pass. No application source or live website model was changed.

Comparison images are cropped for visual inspection; they are not calibrated facial measurement overlays. Use the exact same-camera v21/v22 render pair to assess the geometry change, and the original portrait to judge identity.

## Handoff

Shared project directory: `projects/ZacharyPortfolio/artifacts/avatar-v22-codex-20261030/`.

- `Zachary_Avatar_v22_Review.blend`: editable comparison and authoring scenes, candidate active.
- `zachary_character_v22_candidate.glb`: portable candidate with embedded maps.
- `avatar-v22-reference-comparison.jpg`: original portrait, v21, and v22.
- `avatar-v22-ear.png` / `avatar-v22-ear-left.png`: close ear checks.
- `avatar-v22-validation.json` / `avatar-v22-metrics.json`: measured checks.

Original assets and v21 are retained. No photos were uploaded to an image-generation service, and no source images were edited.
