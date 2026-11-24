# Zachary avatar v32 mouth structure review

Prepared 9 November 2026. This continues the whole-model refinement from v31 and remains a review candidate.

The previous speech deformation stretched a closed lip surface. v32 introduces a narrow rounded lip aperture and a recessed oral cavity, then replaces the mouth-open, jaw-open and AA expression shapes to open that space. The jaw motion tapers at the lip corners. The original lip texture seams are preserved through the cut, preventing dark triangles where the cut crosses the UV seam.

The neutral slit has a nominal maximum height of 0.4 mm. Its recessed back is at glTF Z = 0.060 m, approximately 30–43 mm behind the lip surface. These are modeling choices, not measurements of personal mouth anatomy.

Original face vertex positions, UVs, normals and skin weights retain their values and indices. New vertices are appended. Five existing expression targets retain their original-vertex values; mouthOpen, jawOpen and viseme_aa are revised. Other meshes, rig and texture bytes are preserved. The face triangulation replaces the cut region and removes 471 pre-existing zero-area triangles. The three pre-existing nonmanifold edges around the eyes remain and still need attention.

| Verification scope | Result |
| --- | --- |
| Export preservation, finite values, weights, topology, expression seams and bounds | 147 checks passed; 0 failed |
| New welded boundary or nonmanifold edges | None; original boundary set and nonmanifold edge set preserved |
| New face/cavity seam displacement mismatch across all eight targets | 0 mm |
| New face/cavity seam skin-weight mismatch | 0 |
| Exported GLB | 2,508,120 bytes; 42,026 triangles; 52 joints |
| Texture budget | Five original texture images; each below 100 KB |
| Reopened Blender facial review | Eight expression frames; both morph meshes synchronized |
| Imported facial shape verification | All 2,150 skin vertices and 183 oral vertices checked; maximum delta error below 0.00006 mm |
| Reopened gesture targets | Wrist errors below 0.001 mm |
| Packed review textures | All ten image datablocks packed, representing five source textures across scenes |

Blender verification uses a fresh import of the exported GLB. Neutral, blink, smile, jaw opening, speech, smile with speech, mouth-open and wide-opening states were rendered. Speech was additionally inspected from three-quarter and side views. The neutral appearance is retained closely, and the opening remains continuous in the reviewed poses. The whole-model scene includes a current front render and the established gesture demonstrations. The final Blender file was reopened for data and animation checks.

## Review timeline

The Facial expression review v32 scene contains neutral at frame 1, blink at 41, smile at 81, jaw at 121, speech at 161, smile with speech at 201, mouth-open at 241 and wide opening at 281. The Whole model review v32 scene retains station, adjust-glasses, tablet and presentation poses at frames 1, 41, 81 and 121. Review keyframes are stored in the Blender file, not as animation clips in the GLB.

## Application handoff

The cavity is a separate mesh named SM_Character_OralCavity. The application must drive matching facial target names on both this mesh and SM_Character_Face every frame, including resetting inactive targets. The current single-face-mesh update is not sufficient. The schema-version-3 pose JSON includes this facial contract and retains the arm targets and finger contract from v31. Finger motion remains cached rest quaternion multiplied by a local-X curl, with a 0.55 thumb multiplier.

The public application model and website source were not changed. Browser rendering and interpolation are not verified with v32. The public model hash remains df73e3ad3c62e935962ef6cf82491ccb725a17c82ca0284711fd50b8d647ac08.

## Remaining work

The cavity has no teeth or tongue yet, so the mouth interior appears dark. Lip contour and jaw/cheek deformation remain coarse in close-up, particularly at stronger expressions. Eyelid structure, eye/lip texture resolution, fine hand creasing, raised-elbow cloth deformation, remaining station poses and website integration still require work. The original frontal portrait cannot establish the unseen dental anatomy; any future dental detail will be an artistic approximation unless additional reference is supplied.

Whole-model status remains **NO-SHIP**. Application tests, build, governance and VaultLinter release gates have not been run for this asset-only milestone. No user assistance is currently required. Latest-version records and the immutable v32 archive provide the shared-workstation handoff for Gemini.
