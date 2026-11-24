import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
poses=json.loads((root/'work/poses27.json').read_text())
contract={'schemaVersion':2,'avatarVersion':'v28','armPoseTargets':poses,
 'fingerRotation':{'mode':'rest_quaternion_times_local_axis_rotation','localAxis':[1,0,0],
                   'thumbCurlMultiplier':.55,'cacheRestQuaternionOnLoad':True,'accumulateAcrossFrames':False},
 'integrationStatus':'not integrated into portfolio source'}
(root/'outputs/avatar-v28-pose-targets.json').write_text(json.dumps(contract,indent=2)+'\n')
archive='artifacts/avatar-v28-codex-20261104'
record=json.loads((root/'work/avatar-latest.json').read_text())
record.update(latest_verified_review_version='v28',updated='2026-11-04',archive=archive,
 changes=['Fitted all 30 finger pivots to hand surface midlines and corrected palmward bend axes.',
          'Rebuilt hand weights with bone envelopes and a smooth geodesic cuff blend; preserved all 101 cuff seam vertices.',
          'Retained v27 arm targets and specified rest-relative quaternion finger curl for future application integration.'],
 verification=['82 structural/rest-surface/cuff/weight checks passed, zero failures.',
               'Exported GLBs reviewed in Blender at four curl amounts, both hands, whole-body views and three gestures.',
               'Moderate-curl 99th-percentile edge stretch reduced from 1.946x to 1.188x.',
               'Saved Blender file reopened; gesture and finger animation plus packed textures verified.'],
 next_work=['Fused finger webs, coarse tips and palm pinching','Facial detail and likeness','Raised-elbow garment deformation','Remaining station poses, website integration and release gates'],
 active_work='v28 review complete; next refinement is hand surface geometry and palm pinching')
names=['zachary_character_v28_candidate.glb','Zachary_Avatar_v28_Review.blend','avatar-v28-pose-targets.json']
record['files']={name:{'path':f'{archive}/outputs/{name}','sha256':hashlib.sha256((root/'outputs'/name).read_bytes()).hexdigest()} for name in names}
record['application_model']['sha256']=hashlib.sha256(Path(r'D:\omni-workstation\projects\ZacharyPortfolio\public\models\zachary_character.glb').read_bytes()).hexdigest()
record['application_model']['latest_candidate_integrated']=False
(root/'work/avatar-latest.json').write_text(json.dumps(record,indent=2)+'\n')
lines=['# Latest avatar refinement status','','Latest verified review: **v28**, updated 4 November 2026 by Codex.',
       '',f'Archive: `{archive}`. Whole-model refinement remains in progress; this is not a production release.',
       '', '## Latest files','']+[f'- [{name}]({archive}/outputs/{name})' for name in names]
lines += [f'- [Review, verification and limitations]({archive}/outputs/Avatar-v28-Review.md)',
          f'- [Blender comparison]({archive}/outputs/avatar-v28-finger-comparison.jpg)']
for title,key in [('Changes','changes'),('Verified evidence','verification'),('Remaining work','next_work')]:
    lines+=['',f'## {title}','']+[f'- {value}' for value in record[key]]
lines+=['','## Shared-workstation handoff','',record['active_work']+'.',
        'The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.',
        'v28 finger animation requires rest-quaternion × local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.',
        'The GLB has the rig and weights; the Blender file has keyed review demonstrations. The pose JSON supplies the application contract.',
        'Preserve earlier version directories. Update this record only after a new candidate is exported, checked in Blender and archived.']
(root/'work/AVATAR_LATEST.md').write_text('\n'.join(lines)+'\n')
