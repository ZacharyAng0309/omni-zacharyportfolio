# Zachary avatar v25 hair review

Review candidate prepared on 1 November 2026. The next refinement was selected from the user's broader request to improve the avatar. It focuses on the lumpy hair crown and mottled hair surface visible in v24.

The hair crown received local mesh relaxation with a maximum displacement of 2.20 mm. Shared face/hair boundary vertices remain coincident with v24. A procedural strand field follows the scalp from the part, with subtle color and normal variation. Strand placement is artist-authored and inferred from the front portrait. The original photograph provides limited evidence for the sides and back.

Eight existing hair UV islands were repacked into an additional hair coordinate set. Their shapes are preserved, and their linear atlas scale increased by 3.11 times. The color map uses 2048 pixels per side and the normal map uses 512. Both were baked locally into the portable GLB. Original texture coordinates, rig, weights, expression data, face geometry and glasses geometry passed preservation checks.

| Measured item | Result |
| --- | --- |
| Exported GLB | 1,872,952 bytes |
| Triangle count | 41,883 |
| Hair color map | 60,676 bytes |
| Hair normal map | 64,626 bytes |
| Existing face/body map | 111,206 bytes |
| Structural checks | 92 passed, 0 failed |
| Reversed hair triangles relative to v24 | 0 |
| Glasses intersection checks | 0 face or hair intersections across 5 tested poses |
| WebGL governance audit | 0 violations |

Verification covered mesh/index validity, normal lengths, preservation of existing attributes and rig definitions, the additional UV set, texture routing, embedded texture sizes and the 3 MB GLB budget. Pose checks covered neutral, blink, smile and 15-degree head turns in each direction. The closest sampled ear-support gaps were 1.05 mm and 0.87 mm. The shaft median gaps were 5.94 mm and 6.24 mm.

The final exported GLB was reimported into Blender and rendered from the front, three-quarter and both side cameras under the same lighting as v24. The comparison shows smoother crown contours and less mottling. The strand detail remains stylized. Pale grazing highlights, coarse fringe edges, blurred facial detail and jagged neck texture boundaries are still visible.

**Production QA verdict — NO-SHIP.** The inherited face/body map exceeds the workstation's 100 KB texture limit by 11,206 bytes. The 92 passing checks apply to the stated change scope, including the budgets for the new hair maps. They do not certify that inherited texture limit. Browser lighting, the full animation range and release gates remain pending. Production acceptance requires further work.

`Zachary_Avatar_v25_Review.blend` contains separate v24 and v25 scenes with v25 active. `zachary_character_v25_candidate.glb` is the portable candidate. `avatar-v25-hair-comparison.jpg` compares the front and side hair surfaces using matching cameras.
