import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
contract=json.loads((root/'outputs/avatar-v29-pose-targets.json').read_text());contract['avatarVersion']='v30'
(root/'outputs/avatar-v30-pose-targets.json').write_text(json.dumps(contract,indent=2)+'\n')
archive='artifacts/avatar-v30-codex-20261108'
record=json.loads((root/'work/avatar-latest.json').read_text())
record.update(latest_verified_review_version='v30',updated='2026-11-08',archive=archive,
 changes=['Removed erroneous bridges between middle and ring fingers on both hands, retaining their palm connections.',
          'Transferred UVs and weights to appended cut-surface vertices; retained original vertex indices and attributes.',
          'Cleaned Boolean slivers and verified original cuff boundaries with no additional open or non-manifold edges.'],
 verification=['94 preservation, topology, gap-clearance, UV/weight and size checks passed, zero failures.',
               'All 2,078 active hand vertices agree with Blender skinning within 0.001 mm in six poses.',
               'Both hands reviewed with uniform and independent finger curls; full-body views and gestures rendered.',
               'Final Blender file reopened; six hand-review frames, whole-body gestures and packed images verified.'],
 next_work=['Facial detail and likeness review against the local portrait','Coarse cut rims/fingertips and independent-finger creasing','Raised-elbow garment deformation','Remaining station poses, website integration and release gates'],
 active_work='v30 finger-web repair verified; next focus is facial detail and likeness, with finer hand articulation still pending')
names=['zachary_character_v30_candidate.glb','Zachary_Avatar_v30_Review.blend','avatar-v30-pose-targets.json']
record['files']={name:{'path':f'{archive}/outputs/{name}','sha256':hashlib.sha256((root/'outputs'/name).read_bytes()).hexdigest()} for name in names}
record['application_model']['sha256']=hashlib.sha256(Path(r'D:\omni-workstation\projects\ZacharyPortfolio\public\models\zachary_character.glb').read_bytes()).hexdigest()
record['application_model']['latest_candidate_integrated']=False
(root/'work/avatar-latest.json').write_text(json.dumps(record,indent=2)+'\n')
lines=['# Latest avatar refinement status','','Latest verified review: **v30**, updated 8 November 2026 by Codex.',
       '',f'Archive: `{archive}`. Whole-model refinement remains in progress; this is not a production release.',
       '', '## Latest files','']+[f'- [{name}]({archive}/outputs/{name})' for name in names]
lines += [f'- [Review, verification and limitations]({archive}/outputs/Avatar-v30-Review.md)',
          f'- [Blender comparison]({archive}/outputs/avatar-v30-finger-web-comparison.jpg)']
for title,key in [('Changes','changes'),('Verified evidence','verification'),('Remaining work','next_work')]:
    lines+=['',f'## {title}','']+[f'- {value}' for value in record[key]]
lines+=['','## Shared-workstation handoff','',record['active_work']+'.',
        'The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.',
        'Finger animation remains rest-quaternion × local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.',
        'The GLB has the rig and weights; the Blender file has keyed review demonstrations. The pose JSON supplies the application contract.',
        'The hand review includes independent middle/ring curls at frames 161 and 201. Creasing remains visible in those stress tests.',
        'Preserve earlier version directories. Update this record after each exported, Blender-verified and archived candidate.']
(root/'work/AVATAR_LATEST.md').write_text('\n'.join(lines)+'\n')
