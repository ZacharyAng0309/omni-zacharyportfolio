# Zachary avatar v29 palm surface review

Prepared 6 November 2026. This review continues the whole-model refinement from v28.

The left palm had a triangular dent at rest that became sharper during finger curl. v29 uses localized Laplacian relaxation on the existing palm and proximal-finger surface, selected by the current hand weights and distance along the mesh from the cuff. It also smooths nearby weight transitions and updates normals on the changed patch. The before/after Blender views show the dent substantially reduced both at rest and at moderate curl.

The edit moves and reweights 857 hand vertices, with surface displacement capped at 1.5 mm. All 101 shared cuff vertices retain their positions, normals and weights exactly. Vertex order, triangle topology, texture coordinates, material assignments, embedded texture bytes, facial morphs and the v28 joint transforms are preserved. This is a local surface refinement; the fused finger web is not repaired by it.

| Verification scope | Result |
| --- | --- |
| Asset preservation, cuff continuity, hand normals/weights, triangle validity and size budgets | 83 checks passed, 0 failed |
| Maximum hand surface displacement | 1.50004 mm including floating-point rounding |
| Cuff attachment | All 101 shared vertices preserved |
| Reversed or degenerate triangles introduced | 0 |
| Moderate curl, 99th-percentile edge-length ratio | 1.188 in v28 → 1.151 in v29 |
| Stronger curl, 99th-percentile edge-length ratio | 1.373 in v28 → 1.277 in v29 |
| Stronger curl, maximum edge-length ratio | 1.789 in v28 → 1.711 in v29 |
| Portable GLB | 1,968,404 bytes; 41,883 triangles; all five textures below 100 KB |

The numerical bend comparisons use identical rest-relative finger curls. Ratios of 1 mean unchanged edge length; lower values above 1 mean less stretching. This is not an all-edge improvement: the maximum ratio in the small 0.15-radian curl increases slightly from 1.150 to 1.163, although its 99th percentile improves. These checks do not establish collision freedom or quality in all possible gestures.

The exported GLB was imported and rendered in Blender. Review covers four curl amounts on the right hand, neutral and moderate-curl left-hand views, front/quarter/back whole-model views, and neutral, glasses-adjustment, tablet and presentation poses. Independent skinning calculations agree with Blender at sampled vertices within 0.001 mm. The saved Blender file is reopened to verify the stored whole-model and hand-animation review scenes and packed images.

## Handoff and limitations

The arm pose targets and finger animation convention are retained from v28. Cache each finger's rest quaternion and apply `restQuaternion * localXRotation(curl)`, with the 0.55 thumb multiplier. Do not overwrite absolute Euler X or accumulate the rotation over frames. The GLB stores the rig; keyed review demonstrations are in the Blender file. The pose JSON records the application contract.

Whole-model QA remains **NO-SHIP**. The fused middle/ring finger web, coarse fingertip anatomy, facial detail, raised-elbow cloth compression, remaining station poses and website transitions still need work. The public application model has not been replaced. Website test/build and release gates remain pending. No user input is currently required.
