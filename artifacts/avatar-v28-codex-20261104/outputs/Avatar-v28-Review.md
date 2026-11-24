# Zachary avatar v28 finger articulation review

Prepared 4 November 2026. This is the latest verified review candidate, continuing the whole-model refinement from v27.

Thirty finger pivots were 32–64 mm away from fitted surface midlines. The inherited thumb chain also extended beyond the visible thumb. v28 places joints on midlines measured through the existing hand surfaces and gives each joint a local palmward flexion axis. Joint spacing is an authored anatomical approximation, not a measurement of the user's hands.

The hand weights were rebuilt with bone envelopes around those fitted joints. A smooth blend based on distance along the mesh preserves the original cuff attachment. This updates 1,632 hand vertices while retaining all 101 shared cuff vertices exactly. No surface positions, topology, UV coordinates, facial morphs, materials or texture bytes were changed. The existing fused finger areas and coarse surface remain visible and require later geometry work.

| Verification scope | Result |
| --- | --- |
| Structural preservation, permitted rig/weight changes, cuff attachment and resting surface | 82 checks passed, 0 failed |
| Maximum evaluated resting-surface change | Less than 0.00006 mm |
| Hand influences | At most 4 per vertex, normalized and nonnegative |
| Moderate curl, 99th-percentile edge-length ratio | 1.946 in v27 → 1.188 in v28 |
| Stronger curl, 99th-percentile edge-length ratio | 2.828 in v27 → 1.373 in v28 |
| Independent glTF skinning versus Blender | Less than 0.001 mm at sampled hand vertices and gesture samples |
| Saved Blender file | Reopened; whole-body gestures, finger animation and packed textures verified |
| GLB size and triangle count | 1,968,408 bytes; 41,883 triangles |

The edge-length ratios quantify stretching under the tested uniform curls of 0.35 and 0.60 radians per non-thumb joint. A ratio of 1 means unchanged length. These figures do not prove freedom from collisions, compression or defects in untested motions. Thumb curl uses a 0.55 multiplier in both comparison versions.

Visual checks used exported GLBs imported into Blender 5.2.2 LTS. They covered four right-hand curl amounts from front and outer views, neutral and moderate-curl left-hand views, full-body front/quarter/back views, and the neutral, glasses-adjustment, tablet-hand and presentation poses. The review file retains a whole-model scene and a separate hand-articulation scene, each with keyed demonstrations. Texture images are packed into the file.

## Application handoff

The website has not been switched to this candidate. v28 requires the fitted arm targets and the revised finger rotation convention to be integrated together. For fingers, cache each loaded bone's rest quaternion, then set its quaternion to `restQuaternion * localXRotation(curl)` each update. Apply the 0.55 thumb multiplier. Do not replace absolute Euler X, and do not accumulate curl on the previous frame's quaternion. The supplied `avatar-v28-pose-targets.json` records this contract and the v27 arm targets retained by this version.

The GLB contains the corrected rig and weights. The keyed demonstration animations are in the Blender review file; they are not embedded animation clips in the GLB. The Blender hand-review frames are 1, 41, 81 and 121 for curls 0, 0.15, 0.35 and 0.60. Whole-model frames use the same numbers for neutral, glasses adjustment, tablet and presentation.

## Remaining work

Whole-model QA remains **NO-SHIP**. Fused finger webs, coarse fingertips and palm pinching remain, including a visible crease on the left palm during curl. Facial detail, raised-elbow cloth compression, remaining station poses, motion transitions and browser rendering need further work. Website test/build and release gates remain pending. No user input is currently required to continue.
