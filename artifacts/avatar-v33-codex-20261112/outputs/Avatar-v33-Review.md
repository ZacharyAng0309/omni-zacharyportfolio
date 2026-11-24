# Zachary avatar v33 oral detail review

Prepared 12 November 2026. Review candidate continuing the v32 mouth repair.

v33 adds eight upper and eight lower dental crowns plus a tongue, using rounded Blender geometry and restrained enamel/tissue materials. Lower teeth and tongue follow the mouth-open, jaw-open and AA expressions; upper teeth remain fixed to the head. The tongue fits inside the dental arch. The additions stay hidden in the neutral front view and reveal small tooth edges during speech and smiles.

These forms are an artistic approximation. The original closed-mouth portrait supplies no dental reference, so they do not claim to reproduce the subject's teeth or tongue. The tongue remains subtle under the current mouth lighting. A separate cutaway image exposes the geometry for inspection.

Every existing v32 mesh, material, texture, rig accessor and facial expression buffer is preserved. The changes add three meshes, two materials and no textures. New lower-mouth shapes also include normal deltas for changing orientation.

## Verification

| Scope | Result |
| --- | --- |
| Preservation, new data, topology, weights, bounds, mouth clearance and pairwise intersections | 238 checks passed; 0 failed |
| New meshes | 778 vertices; 1,488 triangles; closed manifold components with outward winding |
| Existing v32 accessors, meshes, materials, skin data and texture bytes | Unchanged |
| Pairwise tooth/tongue triangle intersections | 0 in seven checked poses |
| Front-facing skin-penetration samples | 0 failures across 2,266 samples per pose, seven poses |
| New anatomy visible in neutral front sample check | 0 samples |
| GLB | 2,691,704 bytes; 43,514 triangles; 52 joints |
| Textures | Five existing images, each below 100 KB; no additions |
| Project WebGL governance audit | Passed; 0 violations |

The penetration test samples new mesh vertices and triangle centroids against the facial surface from the front. It is not an exhaustive collision proof for every viewpoint or possible expression blend. Pairwise intersection checks cover upper/lower teeth and tongue at neutral, jaw, speech, smile with speech, wide opening, AA and asymmetric speech.

Fresh Blender imports were rendered in ten expression states: neutral, blink, smile, jaw, speech, smile with speech, mouth-open, wide opening, AA and asymmetric speech. Speech was also inspected from three-quarter and side views. The final Blender file is reopened to verify all five facial meshes, saved expression values, imported shape data, packed textures and existing gesture positions.

The governance command checks the current project source/public assets. v33 remains an archived candidate outside the public model path; its size, texture budget and topology are verified separately. Application tests, build and VaultLinter release gates remain pending.

## Blender and application handoff

Facial expression review v33: frames 1, 41, 81, 121, 161, 201, 241, 281, 321 and 361 correspond to the ten expressions above. Whole model review v33 retains the station and three gesture demonstrations at frames 1, 41, 81 and 121. The GLB contains rig and morph data; the keyed review animation is in the Blender file.

The application must synchronize matching facial target names on SM_Character_Face, SM_Character_OralCavity, SM_Character_UpperTeeth, SM_Character_LowerTeeth and SM_Character_Tongue. Reset inactive values on every mesh. Upper-teeth targets intentionally contain zero deltas. The pose JSON remains schema version 3 and lists all five meshes. Arm targets and the cached-rest-quaternion/local-X finger contract remain applicable.

## QA verdict: NO-SHIP

This is a verified refinement milestone, not a production-ready likeness. Eyelid topology, eye/lip texture softness, lip/cheek deformation, fine hand creasing and raised-elbow clothing still need work. The inherited three eye-area nonmanifold edges remain. Oral anatomy is simplified and lacks individualized gums, palate and dental detail. Website integration and browser interpolation are unverified. The public application model and source have not been replaced by this work.

Blender's live connector was unavailable. Modeling, fresh-import rendering and saved-file verification ran through Blender in background mode. No user assistance was required. The immutable archive and latest-version records provide the shared-workstation handoff for Gemini.
