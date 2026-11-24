# Zachary avatar v27 rig and gesture review

Prepared on 1 November 2026 during the ongoing whole-model refinement.

Blender verification of the portfolio's existing gestures exposed arm crossing and sleeve twisting. The wrist pivots were approximately 89–91 mm from the centers of the hand/garment seams. The elbow pivots were approximately 41–43 mm from the centers of the measured sleeve cross-sections. These positions were inferred from the model's seams and sleeve geometry. They are approximate anatomical controls beneath loose clothing.

The four pivots were realigned. Immediate child transforms and inverse bind matrices were compensated to preserve the resting surface. The three gesture targets were then fitted to the visible hand surfaces, wrist locations, elbow bend planes and palm orientation. The fit favors minimal arm twisting. Geometry, texture coordinates, vertex weights, facial morphs, materials and image bytes remain preserved from v26.

| Verification | Result |
| --- | --- |
| Asset and resting-surface checks | 80 passed, 0 failed |
| Maximum change to the evaluated resting surface | Less than 0.00004 mm |
| Portable GLB | 1,968,348 bytes |
| Triangle count | 41,883 |
| Embedded textures | All below 100 KB, inherited from verified v26 |
| Blender/glTF skinning agreement | Within 0.002 mm across sampled vertices in four poses |
| Saved Blender pose frames | Reopened and verified at frames 41, 81 and 121 |
| Blender texture dependencies | Five images embedded |
| Workstation WebGL governance audit | 0 violations |

The exported GLB was imported into a fresh Blender session. Full-body and portrait reviews were followed by neutral, glasses-adjustment, tablet-hand-position and presentation pose renders. The saved review file was reopened to verify the pose targets and embedded textures. The numerical agreement verifies that Blender is reproducing the glTF rig. Visual review provides separate evidence for the improved poses.

The Blender review timeline contains Neutral at frame 1, Adjust glasses at 41, Inspect tablet at 81 and Present at 121. `avatar-v27-pose-targets.json` contains the fitted target values for later application integration. The GLB supplies the corrected rig. The Blender review supplies the keyed pose demonstrations. Website integration and its interpolation behavior remain pending.

**Whole-model QA verdict — NO-SHIP.** The raised elbow retains compressed cloth folds. Facial detail and fine finger articulation remain coarse. Remaining station poses, motion transitions, browser rendering and release gates still require verification or refinement. This version records verified progress toward the complete model.
