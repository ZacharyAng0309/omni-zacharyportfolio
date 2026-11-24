import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
contract=json.loads((root/'outputs/avatar-v28-pose-targets.json').read_text());contract['avatarVersion']='v29'
(root/'outputs/avatar-v29-pose-targets.json').write_text(json.dumps(contract,indent=2)+'\n')
archive='artifacts/avatar-v29-codex-20261106'
record=json.loads((root/'work/avatar-latest.json').read_text())
record.update(latest_verified_review_version='v29',updated='2026-11-06',archive=archive,
 changes=['Reduced the triangular palm dent with local surface relaxation, capped at 1.5 mm.',
          'Smoothed proximal hand weight transitions and refreshed normals on the edited patch.',
          'Preserved all 101 cuff seam vertices, topology, UVs, textures, facial morphs and v28 joint transforms.'],
 verification=['83 asset-preservation, cuff, normal/weight, triangle-validity and size checks passed, zero failures.',
               'Exported GLB reviewed in Blender across four curls, both hands, full-body views and three gestures.',
               'Moderate/strong-curl 99th-percentile edge ratios improved from 1.188/1.373 to 1.151/1.277.',
               'Saved Blender review reopened; whole-model gestures, finger animation and packed images verified.'],
 next_work=['Repair fused middle/ring finger web and improve coarse fingertip anatomy','Facial detail and likeness','Raised-elbow garment deformation','Remaining station poses, website integration and release gates'],
 active_work='v29 palm refinement verified; next is a localized topology repair of the fused finger web')
names=['zachary_character_v29_candidate.glb','Zachary_Avatar_v29_Review.blend','avatar-v29-pose-targets.json']
record['files']={name:{'path':f'{archive}/outputs/{name}','sha256':hashlib.sha256((root/'outputs'/name).read_bytes()).hexdigest()} for name in names}
record['application_model']['sha256']=hashlib.sha256(Path(r'D:\omni-workstation\projects\ZacharyPortfolio\public\models\zachary_character.glb').read_bytes()).hexdigest()
record['application_model']['latest_candidate_integrated']=False
(root/'work/avatar-latest.json').write_text(json.dumps(record,indent=2)+'\n')
lines=['# Latest avatar refinement status','','Latest verified review: **v29**, updated 6 November 2026 by Codex.',
       '',f'Archive: `{archive}`. Whole-model refinement remains in progress; this is not a production release.',
       '', '## Latest files','']+[f'- [{name}]({archive}/outputs/{name})' for name in names]
lines += [f'- [Review, verification and limitations]({archive}/outputs/Avatar-v29-Review.md)',
          f'- [Blender comparison]({archive}/outputs/avatar-v29-palm-comparison.jpg)']
for title,key in [('Changes','changes'),('Verified evidence','verification'),('Remaining work','next_work')]:
    lines+=['',f'## {title}','']+[f'- {value}' for value in record[key]]
lines+=['','## Shared-workstation handoff','',record['active_work']+'.',
        'The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.',
        'The v28/v29 finger animation convention is rest-quaternion × local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.',
        'The GLB has the rig and weights; the Blender file has keyed review demonstrations. The pose JSON supplies the application contract.',
        'Preserve earlier version directories. Update this record after each exported, Blender-verified and archived candidate.']
(root/'work/AVATAR_LATEST.md').write_text('\n'.join(lines)+'\n')
