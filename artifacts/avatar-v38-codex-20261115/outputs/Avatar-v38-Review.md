# Avatar v38 — crown part and hair strands

15 November 2026. **NO-SHIP:** verified review candidate; likeness and website integration remain unfinished.

## Result and reference assessment

The original frontal portrait shows dark brown curtain hair, a slightly offset part, a fuller right lobe and fine strand groups. v37 had a broadly compatible mass but a continuous cap-like surface. v38 introduces a soft crown-part dip and more legible combed strand groups. These are artistic adjustments from a single frontal photo; side/back grooming remains inferred. No calibrated likeness or biometric score is claimed.

- Proportional crown edit: 130 existing hair vertex copies, maximum 5.448 mm downward movement. No new geometry. Every hair boundary vertex is pinned, including all 135 matched face/hair seam pairs. Minimum triangle orientation cosine 0.939; minimum area ratio 0.885.
- Three scales of directional lock/strand detail flow from a pole tilted toward the frontal part. Warm dark brown color variation, a restrained bump and strand-varying roughness break up the previous smooth surface. A texture-content mask and seam falloff protect skin and the garment patch carried in the original Hair mesh.
- Native Cycles baking uses the existing second UV map. Only the three hair image payloads are replaced: 2048² albedo, 1024² tangent normal and 512² packed roughness/specular. No image generation or external generation service was used.
- The first fine-strand bake lost too much detail. The final material uses a coarser strand scale that remains legible after baking. Normal-map compression has 2.01° 95th-percentile error against the raw bake, 3.32° at the 99th percentile; boundary outliers remain. Parameter quantization is bounded by 0.00784. The normal map now uses EXT_texture_webp, already required by the avatar; browser appearance is still unverified.

## Verification scope

- **337 checks passed, zero failed:** all accessors finite; all except hair POSITION/NORMAL byte-preserved; mesh topology, UVs, skin weights, node/rig transforms, facial targets and unrelated materials preserved; four unrelated image payloads unchanged; seam coincidence, part movement, normals, triangle orientation/area and budgets checked.
- Fresh exported GLB imported into Blender 5.2.2 and rendered from front, quarter, side, top and back. Additional fresh-import facial renders cover neutral, speech, blink with raised brows, and quarter/side speech. Broad rim highlights and residual side/rear surface lumps are still visible; this is not a strand-based groom.
- All fourteen facial poses are retained as review keyframes. The saved Blender file was reopened and all fourteen frames checked across six synchronized facial meshes. Imported morph vertex deltas and packed images verified. Four gesture poses checked numerically, 198 sampled vertices per pose, maximum difference below 0.001 mm. Body/eye geometry was unchanged, so the previous exhaustive eye visibility test was not repeated.
- **Budgets:** 44,910 triangles; 2,551,464 bytes; 52 joints; seven images, each below 100 KB. Current project WebGL governance audit passed with zero violations; it covers project source/public files, while candidate budgets were checked separately.

The live Blender add-on was unavailable; all creation, rendering and saved-file verification used the installed Blender in background mode. No user assistance was required for this pass.

## QA verdict and remaining work

**NO-SHIP.** The part and directional strands are more distinct, but the fringe still has a jagged painted/mesh transition. Loose silhouette strands, a less uniform comb pattern and side/rear volume need more work. Fine hair detail can soften at portfolio camera distance. The original face texture, eye shading, subtle asymmetry and hand/cloth details also remain unfinished.

Untested release gates: browser/Three.js appearance and integration, application tests/build, VaultLinter, and independent side/back likeness. A quantitative image-match score was not used because the reference and review differ in clothing, framing and lighting.

The schema-v4 pose file still requires synchronized morph values on Face, OralCavity, UpperTeeth, LowerTeeth, Tongue and Eyelids; both globes follow Head. The GLB contains mesh/rig/morph data, while the fourteen facial and four gesture review keyframes are stored in Blender. Public portfolio assets and application source are unchanged. v37 remains the rollback baseline.
