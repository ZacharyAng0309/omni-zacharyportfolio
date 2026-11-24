# Avatar v34 — eye surface repair

Verified review candidate, 13 November 2026. Whole-model refinement remains in progress; **NO-SHIP**.

## Changes

- Replaced overlapping connectivity in two eye-area patches while retaining the existing surface positions. Face triangle count falls from 3,415 to 3,399; total avatar count is 43,498.
- Removed all three four-face nonmanifold edges in the face. Existing face and face/oral boundary edge sets are exactly preserved (315 and 196 respectively); the character is not claimed to be watertight.
- Blended updated eye normals into the surrounding face. Full-head renders show a reduced sharp fold above the right eye.
- Corrected blink motion at nine geometric vertices. Maximum adjustment is 0.02930 mm. Original rest positions, skin weights, joints, and the other six face targets are preserved.
- Isolated the original texture layout and the baked eye patches in a 4,096 × 2,048 atlas. All 2,407 unaffected face triangles retain their original UV sampling. The atlas is recompressed, so pixel colors are not byte-identical. The original five embedded texture payloads remain untouched.
- Added 105 UV seam copies with matching positions, normals and skin attributes. Existing ears, glasses, hair, clothes, hands and oral components remain intact.
- The candidate is 2,354,404 bytes. The new atlas is 96,380 bytes; all six texture payloads remain below 100 KB.

## Verification and scope

- **384 checks passed, zero failed:** attribute and unaffected mesh preservation; UV transfer and atlas separation; finite data and valid indices; face/face-oral edge multiplicities and boundaries; preserved source textures and size budgets; blink seam continuity; eight blink/brow combinations with zero repaired-patch inversions.
- Fresh GLB imports rendered in Blender 5.2.2: neutral, full blink, smile, jaw, speech, smile/speech, mouth open, wide opening, AA, asymmetric speech, half blink, both winks, blink with raised brows, plus quarter and side speech views.
- The saved review Blender file was reopened. All 14 expression frames synchronize five facial meshes; all imported morph vertex values and packed images were checked. Four gesture poses also matched the expected skinning; maximum sampled error is below 0.001 mm.
- Project WebGL governance audit: zero violations. This checks current project source/public assets; candidate data budgets were checked separately. Application tests/build, browser integration and VaultLinter release gates have not been run for this milestone.
- Blender ran in the background. The live Blender add-on connection remained unavailable.

## Visual limitations and next work

This is a local connectivity and shading repair, not a reconstruction of anatomical eyelids or eyeballs. The source eye/lip texture remains soft, with baked lighting inherited from the source. The portrait likeness still needs refinement; hairline transitions, cheek/lip motion, individual finger creasing and raised-elbow cloth remain open work. The available reference is frontal, which limits accurate side/back likeness. No new external service or image generation was used for v34.

The rejected whole-face unwrap produced overlapping UV artifacts around the nose and mouth. It is not used by the delivered candidate: unchanged triangles use the original layout, and only repaired eye triangles sample the baked region. The final complete-head render was visually inspected after this correction.

## Files and use

- `zachary_character_v34_candidate.glb`: candidate mesh, rig and morph targets.
- `Zachary_Avatar_v34_Review.blend`: portrait, whole-model gesture and facial-expression review scenes. Facial timeline markers run from frame 1 to 521.
- `avatar-v34-pose-targets.json`: schema-version-3 pose and five-mesh expression contract.
- `avatar-v34-comparison.jpg` and `avatar-v34-expressions.jpg`: Blender-rendered visual reviews.

Drive matching target names on Face, OralCavity, UpperTeeth, LowerTeeth and Tongue; reset inactive targets on all five. Upper-teeth target deltas intentionally remain zero. The public portfolio model and application source have not been replaced. Preserve the v33 archive as the baseline.
