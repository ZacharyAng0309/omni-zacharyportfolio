from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
project=Path('D:/omni-workstation/projects/ZacharyPortfolio')
record=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'))
assert record['latest_verified_review_version']=='v31'
record.update(latest_verified_review_version='v32',updated='2026-11-09',archive='artifacts/avatar-v32-codex-20261109')
record['files']={name:{'path':record['archive']+'/outputs/'+name,'sha256':hashlib.sha256((root/'outputs'/name).read_bytes()).hexdigest()} for name in ['zachary_character_v32_candidate.glb','Zachary_Avatar_v32_Review.blend','avatar-v32-pose-targets.json']}
record['changes']=['Introduced a rounded lip opening and recessed oral cavity instead of stretching a closed mouth surface.','Revised mouthOpen, jawOpen and viseme_aa, softened lip-corner motion, and preserved lip texture seams.','Preserved original face vertex attributes and five other expression targets; other meshes, rig and textures are unchanged.']
record['verification']=['147 export, preservation, weights, topology and morph-seam checks passed; zero failures.','Fresh exported GLB reviewed in Blender across eight facial poses plus three-quarter and side speech views.','Final Blender file reopened: both facial meshes synchronized; all imported morph vertices, packed textures and gesture positions verified.','No new welded boundary or nonmanifold edges; pre-existing eye-area topology issues remain.']
record['next_work']=['Add and refine oral anatomy, lip contour and jaw/cheek deformation','Improve eyelid structure and soft eye/lip texture','Refine independent finger creasing and fingertip detail','Raised-elbow cloth, remaining station poses, website integration and release gates']
record['active_work']='v32 structural mouth repair verified; next focus is oral anatomy, eyelids and facial detail. Both facial meshes must be driven together during application integration.'
record['application_model']['latest_candidate_integrated']=False
(root/'work/avatar-latest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified review: **v32**, updated 9 November 2026 by Codex.','','Archive: `'+record['archive']+'`. Whole-model refinement remains in progress; this is not a production release.','','## Latest files','']
for name in record['files']:lines.append(f'- [{name}]({record["archive"]}/outputs/{name})')
for name,label in [('Avatar-v32-Review.md','Review, verification and limitations'),('avatar-v32-mouth-review.jpg','Blender mouth review')]:lines.append(f'- [{label}]({record["archive"]}/outputs/{name})')
for title,key in [('Changes','changes'),('Verified evidence','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+value for value in record[key]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'The cavity has no teeth or tongue yet. Close-up lip and cheek deformation, eyelid structure and the soft face texture remain unfinished.','The public portfolio model is unchanged by this milestone. Read avatar-latest.json for file hashes.','Drive matching target names on SM_Character_Face and SM_Character_OralCavity every frame. The existing single-face-mesh update needs adaptation.','Finger animation remains cached rest quaternion multiplied by local-X curl, with thumb multiplier 0.55. Absolute Euler-X replacement is incompatible.','The pose JSON is schema version 3 and adds the facial synchronization contract. The GLB has the rig and facial targets; the Blender file has keyed facial and gesture reviews.','Preserve earlier version directories. Update this record after each exported, Blender-verified and archived candidate.','']
(root/'work/AVATAR_LATEST.md').write_text('\n'.join(lines),encoding='utf-8')
