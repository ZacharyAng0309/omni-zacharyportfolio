# Zachary avatar v31 blink and facial review

Prepared 8 November 2026. This review continues the whole-model refinement from v30.

The facial audit found that a full blink pulled upper-face vertices into the eyelid closure. Eight shared face/hair seam vertices moved by as much as 2.79 mm, opening small tears near the eyebrows and fringe. v31 narrows the upper reach of the blink deformation while keeping a smooth lower transition. The shared seam now remains fixed, and the visible eyebrow/forehead distortion is reduced.

Only the two blink position targets change. Neutral geometry, all other expression targets, topology, UVs, skin weights, rig transforms, materials and texture bytes are preserved. The existing soft face texture and mouth-opening behavior are not corrected by this milestone.

| Verification scope | Result |
| --- | --- |
| Morph isolation, neutral asset preservation, blink bounds, seam protection, eye closure and size limits | 87 checks passed, 0 failed |
| Maximum shared face/hair seam movement during blink | 2.79 mm in v30 → 0 mm in v31 |
| Shared face/hair vertex copies checked | 128 |
| Protected upper-face displacement | Reduced from up to 7.45 mm to 0 mm |
| Sampled eye-aperture closure | More than 95% vertical closure retained on both sides |
| Lower blink transition compared with v30 | Maximum difference below 0.25 mm |
| Portable GLB | 2,097,476 bytes; 42,135 triangles |

Blender verification uses the exported GLB. It includes neutral, half-blink, full blink, unilateral wink, blink plus brow raise, and a three-quarter blink view. The broader facial audit also inspected smile, jaw-open and speech poses. Whole-model views and the existing gesture demonstrations are retained in the final review file, which is reopened to check animation values and packed textures.

## Reference and limitations

The original portrait remains local. Coarse camera/framing comparison uses normalized head crops and a transparent head-only Blender render. That comparison passes the workstation's silhouette gate (IoU 0.9566, aspect drift 0.0333). These are coarse framing measurements, not a likeness score or proof of matching facial anatomy. The opaque full-character crop is retained as an earlier diagnostic and is not used for the head-only comparison.

The review confirms two remaining facial issues. The eye and lip texture is substantially softer than the portrait, and the speech pose stretches a closed lip surface instead of revealing a modeled mouth cavity. Outer eyelid creasing also remains coarse. A structural mouth/eyelid pass is needed before detailed texture refinement can be considered complete.

Whole-model QA remains **NO-SHIP**. Fine hand articulation, facial detail, mouth anatomy, raised-elbow cloth deformation, remaining station poses, website integration and release gates still require work. The public application model has not been replaced. No user assistance is currently required.

## Blender and application handoff

The facial-review timeline contains Neutral at frame 1, Half blink at 41, Full blink at 81, Left wink at 121 and Blink plus brow at 161. The whole-model scene retains its neutral and three gesture demonstrations. The GLB contains the corrected facial targets; review keyframes remain in the Blender file.

The v30 arm targets and finger rotation contract remain applicable. Cache each finger rest quaternion and apply rest-quaternion × local-X curl, with a 0.55 thumb multiplier. Browser rendering and interpolation have not yet been verified with this candidate.
