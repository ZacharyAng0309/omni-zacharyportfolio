# Avatar v42 — crown and fine-strand refinement

19 November 2026. **NO-SHIP as a production update:** verified Blender review candidate. The integrated application remains v41.

## Result

This is a subtle hair finishing pass based on Antigravity's integrated v41. Local Laplacian relaxation softens small crown facets, moving 653 hair vertex copies by at most 1.800 mm. The lower fringe geometry and every original Face/Hair seam position remain fixed. The v41 face/chin, eyes, eyelids, spectacles, ears, skin textures, original rig weights and facial morph data are preserved.

Thirty-eight sparse round filaments add fine fringe ends and crown flyaways: 28 along the existing curtain fringe and 10 over the crown. Their widths taper toward the tips; roots embed into the existing surface. They use opaque vertex colors, smooth normals, and nearest-surface barycentric skin-weight transfer. All 1,256 new vertices follow the existing Head joint exactly. There is no alpha layer, texture-resolution increase, new image, bone or facial channel.

The added mesh is `SM_Character_HairFilaments`, with `M_Hair_Filaments_v42`. It adds 2,360 triangles and one material/draw call. The first thicker/darker strand trial was rejected during the Blender comparison; only the finer final version is included. The overall hairstyle is still stylized and the underlying painted fringe remains. This does not constitute a full groom or a calibrated likeness match. The original front photograph guided the part and flow; crown/side depth is inferred from one view.

## Verification scope

- **449 preservation, geometry and rig checks passed; zero failed.** Every original accessor is byte-equivalent as decoded except the crown's Hair position/normal arrays. All original materials, textures, seven embedded image payloads, UV sets, joint data, morph targets and mesh definitions are retained. The 155 Face/Hair seam vertex copies retain their positions.
- The new filaments are closed manifold tubes, with consistent outward winding, positive enclosed volumes, unit normals, nondegenerate triangles, valid indices and normalized skin weights. Original hair triangles retain orientation and bounded area ratios.
- Fresh exported GLB imported into Blender and rendered from front, quarter, side, top and back. Facial renders cover neutral, smile, speech, asymmetric speech, blink with raised brows, and quarter/side speech. Identical lighting and cameras provide the v41/v42 comparison. Live Blender MCP remained unavailable; Blender 5.2.2 background rendering and file reopen supplied the verification.
- The final `.blend` reopened with all fourteen facial frames synchronized across six meshes, all imported morph positions verified, fourteen packed image datablocks, and four gesture poses checked. Gesture samples and wrist-target comparisons remained below 0.001 mm.
- Head-yaw and pitch checks tested every imported filament vertex across three rotations: maximum difference from the expected Head transform was 0.000123 mm. The exposed distal fringe was sampled at 65 points against the fully raised-brow forehead; the conservative minimum clearance was 0.105 mm. This is a sampled clearance check, not a continuous collision proof.
- **Budgets:** 47,270 triangles; 2,678,460 bytes; 52 joints; seven images, all below 100 KB. The candidate is below 3.0 MB. The project WebGL governance audit passed with zero violations.

## Remaining work and integration limits

The browser-integrated v41 is unchanged. v42 has not been checked in the application's lighting, anti-aliasing or device performance. The existing application applies its special hair material calibration only to the exact `SM_Character_Hair` mesh name; evaluate the new `SM_Character_HairFilaments` material under that lighting before integration. Fine fibers may require distance-dependent visibility or an LOD policy. Application tests/build and VaultLinter release gates were not rerun for this Blender-only pass.

Broader hair clump volume and fringe outline, native collar/wrist atlas margins, residual skin/cloth facets, and hand detail remain refinement work. The raw Blender GLB still shows the inherited collar atlas triangles that v41's application shader masks; this pass does not claim to repair that asset-level issue. No Higgsfield or image-generation service was used.

## Handoff

The archive contains the v41 rollback GLB, authored strand paths/mesh arrays, build and verification scripts, source-state snapshot, final renders and saved Blender review. Reproduction: `hair42-build.py` in Blender → `hair42-embed.py` → `verify42.py` → fresh Blender import/render → expression/whole-model review → saved-file reopen. Base-color UV2 and normal/parameter UV1 remain unchanged. Pose schema v4 and its six facial meshes are retained.
