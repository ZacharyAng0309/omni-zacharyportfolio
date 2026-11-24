# Avatar v36 — separate eyes and fitted eyelids

14 November 2026. **NO-SHIP:** verified review candidate; likeness and website integration remain unfinished.

## Structural change

The former eyes were texture painted onto a continuous face surface. v36 replaces 277 triangles inside two local socket patches with real openings, a fitted eyelid mesh and two separate closed eye globes. The eyelid mesh has four concentric loops per eye, a transition into the original irregular boundary, and a thin inner rim. Skin color is baked from the existing face with Blender Cycles onto a new UV layout. The globes use dark pupil/iris and muted sclera vertex colors; these are artistic approximations, not a scan of personal eye anatomy.

Neutral opening height was reduced after the first prototype looked too wide-eyed. Existing outer-face blink targets gain depth movement so the lids pass over the globe surface. The new inner lid rings meet on a shared contact line; rim thickness is retained. Raised-brow influence tapers out before this contact line. Triangulation and float precision at the contact line were checked after export, fixing two folding quads and thin-rim artifacts found during iteration.

The original face rest positions, normals, UVs and skin weights are preserved. Six existing face targets are unchanged; only the two blink POSITION targets gain depth motion. Original materials and all six original image payloads remain unchanged. Ears, hair, glasses, hands, clothes and oral meshes retain their prior data. Three meshes are added: Eyelids, EyeLeft and EyeRight. The eyes follow Head and do not yet have independent gaze controls.

## Verification and limits

- **1177 checks passed, zero failed.** Scope: original data/material/texture preservation, existing node transforms, finite arrays, weights/normals, original/new skin boundary correspondence for all eight targets, globe edge topology, texture/asset budgets, and sampled eye visibility.
- **Ten numeric eye cases:** neutral, quarter/half/three-quarter/full blink, full blink with raised brows, both winks, raised brows and speech. Zero eye samples protruded through skin outside the intended opening. Full blink and blink+brow hid every sampled globe point. These finite ray samples do not constitute an exhaustive surface-intersection proof.
- No zero-area eyelid triangles in checked poses; eyelid front triangles retain their projected orientation (the closed rim can turn edge-on). Combined Face + Eyelids + OralCavity has zero nonmanifold edges and exactly 64 additional boundary edges for the two intended eye openings. Other pre-existing skin boundaries remain; no claim that the whole character is watertight.
- Fresh exported GLB rendered in Blender: fourteen expression poses, quarter/side speech, portrait front/quarter and the full body. Four gesture poses were checked numerically. The saved Blender file was reopened: all fourteen facial frames synchronize **six** facial meshes; every imported morph vertex was compared with the GLB, images are packed, and gesture wrist errors remain below 0.001 mm.
- **Budgets:** 44,910 triangles; 2,547,820 bytes; 52 joints. Seven image payloads, all below 100 KB. Eyelids: 345 vertices/537 triangles. Each closed eye globe: 290 vertices/576 triangles.
- Project WebGL governance audit passed with zero violations. It covers current project source/public assets; candidate budgets were checked separately. Application/browser integration, tests/build and VaultLinter release gates remain pending.

Blender 5.2.2 was run in the background. The live add-on connection was unavailable. No external generation service was used and no user assistance was needed for these checks.

## Visual assessment and next work

This is a structural eye upgrade with a noticeably different neutral appearance. It is not final photorealistic likeness. Iris variation/cornea appearance, pupil/iris proportions and upper-lid folds need further refinement against the portrait. The skin texture remains soft and contains inherited shading. Side/back anatomy is approximate with only the frontal reference available. Lip/cheek motion, oral detail, finger creasing and raised-elbow cloth also remain open work.

## Integration contract

`avatar-v36-pose-targets.json` uses **schema version 4**. Drive matching facial target values on Face, OralCavity, UpperTeeth, LowerTeeth, Tongue **and Eyelids**, resetting inactive values on all six each frame. Updating only the old five meshes will break blink closure. EyeLeft/EyeRight are head-skinned static globes and have no morph targets. Existing arm/finger pose rules remain applicable.

`Zachary_Avatar_v36_Review.blend` contains the portrait, whole-model gesture and facial-expression scenes. Facial markers span frames 1–521. The GLB contains rig and morph data; review timeline keyframes are stored in Blender. The public portfolio model and source are unchanged. Preserve the v35 archive as the rollback baseline.
