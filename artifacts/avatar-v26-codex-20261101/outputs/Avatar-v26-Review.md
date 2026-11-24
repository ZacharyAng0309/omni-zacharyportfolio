# Zachary avatar v26 material and whole-model review

Prepared on 1 November 2026 as part of the ongoing whole-model refinement.

The whole-body audit found abrupt material color changes at the neck, ears and cuffs. Some skin pixels were receiving the hair tint, and a fabric UV island with 207 vertices and 54 shared garment vertices was being treated as hair. The repair uses original texture content and the existing garment seam to align skin and fabric colors, roughness and specular response. The color treatment is an artistic approximation based on the source asset.

The new diffuse maps were baked without scene lighting. Roughness and specular strength share packed parameter textures. Original texture content still carries some inherited lighting and blur. Every geometry, topology, normal, texture-coordinate, skin-weight and morph accessor passed exact preservation checks against v25.

| Verification | Result |
| --- | --- |
| Structural and material checks | 86 passed, 0 failed |
| Mean RGB discontinuity at 41 sampled neck boundary points | 18.362 to 1.376 on a 0–255 scale |
| Mean RGB discontinuity at 101 sampled cuff boundary points | 5.763 to 0.367 on a 0–255 scale |
| Face texel compression error against the lossless bake | Mean 0.987, 99th percentile 4.0 on a 0–255 scale |
| Embedded texture sizes | 90,724 / 80,324 / 64,626 / 67,256 / 28,163 bytes |
| Portable GLB | 1,968,328 bytes |
| Workstation WebGL governance audit | 0 violations |

The exported GLB was reopened in Blender. Verification included front, three-quarter and both side portraits, full-body front/three-quarter/back views, and a hand/cuff close-up. All embedded textures now meet the 100 KB target. The Blender file contains portrait comparison scenes and a retained whole-model review scene.

The movement audit revealed a separate major problem in the portfolio's named pose targets. The glasses gesture crosses the body, and the tablet gesture twists the sleeves. The independent Blender skinning reconstruction agreed with glTF calculations within 0.002 mm at the sampled vertices, supporting the pose diagnosis. Wrist pivot inspection subsequently measured approximately 89–91 mm offsets from the hand/garment seam centers. These findings drive the next rig refinement.

**Whole-model QA verdict — NO-SHIP.** Facial detail, finger articulation, rig/presentation gestures, browser rendering and final release gates still require work. The material correction is a verified milestone within that larger goal.
