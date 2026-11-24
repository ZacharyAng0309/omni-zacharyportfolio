from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];out=root/'outputs';work=root/'work'
validation=json.loads((work/'eye34-validation.json').read_text());blend=json.loads((work/'blend34-validation.json').read_text());changes=json.loads((work/'eye34-changes.json').read_text());blink=json.loads((work/'eye34-blink-changes.json').read_text())
assert validation['checks_failed']==0 and blend['morph_meshes_synchronized']==5
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
contact=Image.new('RGB',(1080,650),(35,35,35));draw=ImageDraw.Draw(contact)
for col,(label,path) in enumerate([('Previous review — v33',work/'oral33-neutral.png'),('Eye repair — v34',work/'expression34-neutral.png')]):
 im=Image.open(path).convert('RGB').resize((540,600),Image.Resampling.LANCZOS);contact.paste(im,(540*col,50));draw.text((540*col+20,12),label,font=font,fill='white')
contact.save(out/'avatar-v34-comparison.jpg',quality=92)
labels=['neutral','half-blink','blink','blink-brow','left-wink','right-wink','smile-speech','speech-quarter']
contact=Image.new('RGB',(1200,748),(35,35,35));draw=ImageDraw.Draw(contact)
for i,label in enumerate(labels):
 x=i%4*300;y=i//4*374;im=Image.open(work/f'expression34-{label}.png').convert('RGB').resize((300,333),Image.Resampling.LANCZOS);contact.paste(im,(x,y+41));draw.text((x+12,y+9),label.replace('-',' ').title(),font=font,fill='white')
contact.save(out/'avatar-v34-expressions.jpg',quality=92)
(out/'Avatar-v34-Review.md').write_text(f'''# Avatar v34 — eye surface repair

Verified review candidate, 13 November 2026. Whole-model refinement remains in progress; **NO-SHIP**.

## Changes

- Replaced overlapping connectivity in two eye-area patches while retaining the existing surface positions. Face triangle count falls from 3,415 to 3,399; total avatar count is 43,498.
- Removed all three four-face nonmanifold edges in the face. Existing face and face/oral boundary edge sets are exactly preserved (315 and 196 respectively); the character is not claimed to be watertight.
- Blended updated eye normals into the surrounding face. Full-head renders show a reduced sharp fold above the right eye.
- Corrected blink motion at nine geometric vertices. Maximum adjustment is {max(r['max_adjustment_mm'] for r in blink):.5f} mm. Original rest positions, skin weights, joints, and the other six face targets are preserved.
- Isolated the original texture layout and the baked eye patches in a 4,096 × 2,048 atlas. All 2,407 unaffected face triangles retain their original UV sampling. The atlas is recompressed, so pixel colors are not byte-identical. The original five embedded texture payloads remain untouched.
- Added 105 UV seam copies with matching positions, normals and skin attributes. Existing ears, glasses, hair, clothes, hands and oral components remain intact.
- The candidate is {validation['metrics']['glb_bytes']:,} bytes. The new atlas is {changes['baked_texture_bytes']:,} bytes; all six texture payloads remain below 100 KB.

## Verification and scope

- **{validation['checks_passed']} checks passed, zero failed:** attribute and unaffected mesh preservation; UV transfer and atlas separation; finite data and valid indices; face/face-oral edge multiplicities and boundaries; preserved source textures and size budgets; blink seam continuity; eight blink/brow combinations with zero repaired-patch inversions.
- Fresh GLB imports rendered in Blender 5.2.2: neutral, full blink, smile, jaw, speech, smile/speech, mouth open, wide opening, AA, asymmetric speech, half blink, both winks, blink with raised brows, plus quarter and side speech views.
- The saved review Blender file was reopened. All {len(blend['facial_frames_verified'])} expression frames synchronize five facial meshes; all imported morph vertex values and packed images were checked. Four gesture poses also matched the expected skinning; maximum sampled error is below 0.001 mm.
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
''',encoding='utf-8')
project=Path('D:/omni-workstation/projects/ZacharyPortfolio');record=json.loads((project/'avatar-latest.json').read_text(encoding='utf-8-sig'));assert record['latest_verified_review_version']=='v33'
archive='artifacts/avatar-v34-codex-20261113'
record.update(latest_verified_review_version='v34',updated='2026-11-13',archive=archive)
names=['zachary_character_v34_candidate.glb','Zachary_Avatar_v34_Review.blend','avatar-v34-pose-targets.json','Avatar-v34-Review.md','avatar-v34-comparison.jpg','avatar-v34-expressions.jpg','full34-front.png','full34-audit.json']
record['files']={name:{'path':archive+'/outputs/'+name,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()} for name in names}
record['changes']=['Repaired eye-patch connectivity: three nonmanifold edges removed without moving rest positions.','Isolated baked eye texture from original face UVs; corrected corner inversions during blink and brow combinations.','Preserved other anatomy and six non-blink targets; 2.35 MB review candidate.']
record['verification']=[f"{validation['checks_passed']} checks passed; zero failed, including source preservation, UV transfer, topology and blink/brow combinations.",'Final exported GLB rendered in Blender across fourteen expressions plus quarter/side speech views.','Saved Blender file reopened; five synchronized facial meshes, morph data, packed images and gesture targets verified.','Current project governance audit passed with zero violations; candidate budgets checked separately.']
record['next_work']=['Anatomical eyelids, eye texture and hairline transitions','Cheek/lip motion and individualized oral anatomy','Independent finger creasing, fingertip detail and raised-elbow cloth','Remaining station poses, application integration and release gates']
record['active_work']='v34 eye connectivity, UV isolation and blink/brow repair verified. Next focus: anatomical eyelid structure and soft facial texture. Five facial meshes must remain synchronized.'
record['application_model']['latest_candidate_integrated']=False
(work/'avatar-latest-v34.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['# Latest avatar refinement status','','Latest verified review: **v34**, updated 13 November 2026 by Codex.','','Whole-model refinement remains in progress; not a production release.','','## Files','']
lines += [f'- [{name}]({record["files"][name]["path"]})' for name in names]
for title,field in [('Changes','changes'),('Verification','verification'),('Remaining work','next_work')]:lines+=['','## '+title,'']+['- '+v for v in record[field]]
lines+=['','## Shared-workstation handoff','',record['active_work'],'The public portfolio model is unchanged. Application/browser and release checks remain pending. The GLB has rig/morph data; review keyframes are in the Blender file. Preserve prior immutable archives.','']
(work/'AVATAR_LATEST-v34.md').write_text('\n'.join(lines),encoding='utf-8')
print('DELIVERY_READY',names)
