import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
contract=json.loads((root/'outputs/avatar-v30-pose-targets.json').read_text());contract['avatarVersion']='v31'
(root/'outputs/avatar-v31-pose-targets.json').write_text(json.dumps(contract,indent=2)+'\n')
archive='artifacts/avatar-v31-codex-20261108'
record=json.loads((root/'work/avatar-latest.json').read_text())
record.update(latest_verified_review_version='v31',updated='2026-11-08',archive=archive,
 changes=['Restricted the upper blink deformation to protect the eyebrows, forehead and shared hairline seam.',
          'Reduced blink seam motion from 2.79 mm to zero while retaining sampled eye closure above 95 percent.',
          'Preserved neutral geometry and all six other expression targets; audited the remaining mouth and texture defects.'],
 verification=['87 morph-isolation, preservation, seam, closure and size checks passed, zero failures.',
               'Exported GLB reviewed in Blender for partial/full blinks, wink, brow combination and three-quarter closure.',
               'Coarse normalized head framing passed the reference silhouette gate; this is not a likeness score.',
               'Final Blender file reopened; facial animation, whole-model gesture frames and packed textures verified.'],
 next_work=['Repair the closed mouth surface and missing oral cavity exposed by the speech pose','Improve eyelid structure and soft eye/lip texture','Refine independent finger creasing and fingertip detail','Raised-elbow cloth, remaining station poses, website integration and release gates'],
 active_work='v31 blink seam correction verified; next focus is structural mouth and eyelid refinement')
names=['zachary_character_v31_candidate.glb','Zachary_Avatar_v31_Review.blend','avatar-v31-pose-targets.json']
record['files']={name:{'path':f'{archive}/outputs/{name}','sha256':hashlib.sha256((root/'outputs'/name).read_bytes()).hexdigest()} for name in names}
record['application_model']['sha256']=hashlib.sha256(Path(r'D:\omni-workstation\projects\ZacharyPortfolio\public\models\zachary_character.glb').read_bytes()).hexdigest()
record['application_model']['latest_candidate_integrated']=False
(root/'work/avatar-latest.json').write_text(json.dumps(record,indent=2)+'\n')
lines=['# Latest avatar refinement status','','Latest verified review: **v31**, updated 8 November 2026 by Codex.',
       '',f'Archive: `{archive}`. Whole-model refinement remains in progress; this is not a production release.',
       '', '## Latest files','']+[f'- [{name}]({archive}/outputs/{name})' for name in names]
lines += [f'- [Review, verification and limitations]({archive}/outputs/Avatar-v31-Review.md)',
          f'- [Blender blink comparison]({archive}/outputs/avatar-v31-blink-comparison.jpg)']
for title,key in [('Changes','changes'),('Verified evidence','verification'),('Remaining work','next_work')]:
    lines+=['',f'## {title}','']+[f'- {value}' for value in record[key]]
lines+=['','## Shared-workstation handoff','',record['active_work']+'.',
        'The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.',
        'Finger animation remains rest-quaternion × local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.',
        'The GLB has the rig and facial targets; the Blender file has keyed facial/gesture reviews. The pose JSON supplies the application contract.',
        'The speech pose is still a closed-surface deformation. Do not treat it as a finished mouth-opening implementation.',
        'Preserve earlier version directories. Update this record after each exported, Blender-verified and archived candidate.']
(root/'work/AVATAR_LATEST.md').write_text('\n'.join(lines)+'\n')
