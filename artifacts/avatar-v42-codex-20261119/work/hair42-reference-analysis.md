# v42 hair refinement brief

The source is the user's frontal studio portrait: dark-brown curtain hair, a slightly left-offset part, a larger right lobe, curved overlapping fringe and a few fine crown flyaways. The front is the only observed view; side and rear details are inferred. The v41 face, eyes, eyelids, glasses, skin, weights and morph targets are protected.

The current hair has a broadly appropriate curtain silhouette, but its continuous crown and painted fringe edge read as a solid cap. This pass softens small crown facets with bounded local Laplacian relaxation and trials sparse, tapered, round filaments following the existing locks. These are actual three-dimensional fibers, with roots embedded into the hair and weights transferred from its nearest surface. No wide overlay ribbons, new texture images or face repainting are used.

Compare the v41 baseline and candidate using identical front/quarter/side/top/back Blender cameras and lighting. Inspect the exported GLB freshly imported into Blender, and evaluate forehead clearance under raised brows. This is an incremental review, not a full photoreal groom or a production release. The browser-integrated v41 remains authoritative for the application until the new candidate has its own integration checks.
