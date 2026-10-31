# Zachary avatar v23 — glasses fit and front ear silhouette

Review candidate, 31 October 2026. No change to the model served by the portfolio.

**Cause.** An earlier workstation script lowered the upper ears and clipped the sides of the head to make room for the glasses. The v22 model inherited that shape. Its reimported glasses also intersected the face in 18 triangle pairs in the neutral pose.

**Correction.** Matched v22 texture coordinates to the pre-compression v19 mesh and restored part of the earlier ear and temple volume with a gradual falloff across shared face/hair vertices. This uses existing 3D anatomy, not a projection of the portrait or a new mirrored ear. Refit the two metal arms and tips to separately sampled cross-sections of the restored head. Retained the lens geometry, bridge, image maps, skin weights, expressions and rig. A first outward adjustment was rejected after rendering because the arms visibly flared.

**Measurements.** In the same lateral ear-region sample on the two sides, the vertical span changed from 47.95 to 59.60 mm and from 46.32 to 56.35 mm. These are model-region measurements, not measurements of the subject. At the central shafts, the median sampled surface gaps were 5.94 and 6.24 mm; near the ear supports, the closest sampled gaps were 0.80 and 0.77 mm. Local front projection is improved; the reference portrait does not establish exact ear depth or physical fit.

**Verification.** Reimported the saved GLB into clean Blender scenes, compared it with v22 under identical front, three-quarter and opposing side cameras, and reopened the saved Blender file. Mesh intersection checks found zero face/glasses and hair/glasses overlapping triangle pairs in neutral, blink, smile and both tested 15-degree head poses. The model passed 76 structural checks (including preserved rig/mesh definitions, unedited attributes, unchanged embedded image data, valid topology and unit normals). No changed face/hair triangle normal rotated more than 90 degrees from v22 in the neutral geometry diagnostic. The GLB is 1,821,552 bytes; the workstation governance audit reported 0 violations. No application source changed, and no application test suite was run.

**Review status.** Ready for visual review; not a release or a photographic reconstruction of the inner ear. The scan still has coarse rim and skin detail. Browser lighting, full animation range, nose-pad contact and subjective likeness have not been independently certified in this pass.

The Blender file contains separate v22 and v23 comparison scenes. The three-panel front comparison is cropped to approximately align the eyes with the original portrait; it is not a calibrated biometric overlay.
