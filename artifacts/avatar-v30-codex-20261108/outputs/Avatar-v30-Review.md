# Zachary avatar v30 finger-web repair

Prepared 8 November 2026. This review continues the whole-model refinement from v29.

Both hands had unwanted surface bridges between the middle and ring fingers. v30 opens those gaps using a narrow, rounded cut aligned with the observed separation. The anatomical finger bases remain attached to the palm. Cut surfaces receive transferred texture coordinates and skin weights. Original vertex indices and attributes are retained, with new vertices appended for the repair.

The repair preserves 2,605 of the original 2,723 hand triangles and replaces the affected web region. It adds 398 vertices, including texture-seam duplicates, and increases the total model from 41,883 to 42,135 triangles. Two tiny sliver faces produced by Boolean triangulation were removed before validation. The final surface has the original cuff boundaries and no additional open or non-manifold edges.

| Verification scope | Result |
| --- | --- |
| Non-hand preservation, original hand attributes, topology, gap clearance, UVs, weights and size budgets | 94 checks passed, 0 failed |
| Original hand vertex attributes and order | Preserved exactly |
| Existing cuff boundary | Same 95 geometric edges; no new open edges |
| Hand connectivity | Two connected hands retained |
| Erroneous topology handles | Two removed; combined Euler characteristic changes from −2 to 2 |
| Gap clearance at four sampled heights | Original bridges intersected all four probes; repaired gap clears all four |
| Blender versus independent skinning calculation | All 2,078 active hand vertices checked in six poses; maximum difference below 0.001 mm |
| Portable GLB | 2,097,476 bytes; 42,135 triangles; five textures below 100 KB each |

Blender review includes four uniform curls on the right hand, neutral/moderate left-hand views, and separate middle-only and ring-only curls on both hands. These are followed by full-body front/quarter/back views and neutral, glasses-adjustment, tablet and presentation poses. The gap remains open in the reviewed bend views. The saved Blender review is reopened to verify its retained scenes, animation and packed textures.

The hand review timeline uses frames 1, 41, 81 and 121 for uniform curls 0, 0.15, 0.35 and 0.60. Frames 161 and 201 demonstrate independent middle and ring finger curls. The whole-model scene retains its four established gesture frames. Review animations are stored in the Blender file; the GLB supplies the model and rig without embedded animation clips.

## Handoff and remaining work

The v28/v29 arm targets and rest-relative finger convention remain applicable. Cache each finger bone's loaded rest quaternion and apply `restQuaternion * localXRotation(curl)`, with a 0.55 thumb multiplier. The pose JSON records this contract. The public application model has not been replaced.

Whole-model QA remains **NO-SHIP**. The cut rims and fingertips still have coarse geometry, and independent curls expose some creasing and local stretching. In the independent-finger stress poses, maximum edge ratios reach roughly 3.44–3.67; the topology repair does not establish polished articulation in arbitrary poses. Facial detail and likeness, raised-elbow cloth compression, remaining station poses, website transitions and release gates also remain pending. No user input is currently required to continue.
