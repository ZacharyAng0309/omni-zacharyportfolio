from pathlib import Path
p=Path('work/archive32.ps1').read_text()
p=p.replace('v32','v33').replace('v31','v32').replace('20261109','20261112').replace('2026-11-09','2026-11-12').replace('mouth32-validation','oral33-validation').replace('blend32-validation','blend33-validation').replace('archive32-validation','archive33-validation')
p=p.replace('-ne 2','-ne 5').replace("-match '32'","-match '33'").replace('avatar_v33_mouth_review','avatar_v33_oral_review').replace('full32','full33')
p=p.replace("'avatar-v33-mouth-review.jpg','full33", "'avatar-v33-mouth-review.jpg','avatar-v33-oral-cutaway.png','full33")
p=p.replace('Avatar-v33-Mouth','Avatar-v33-Oral').replace('Avatar mouth opening and oral cavity review','Avatar oral detail and clearance review').replace('Avatar v33 Mouth Structure Review','Avatar v33 Oral Detail Review').replace('Mouth structure review - 9 November 2026','Oral detail review - 12 November 2026')
start=p.index("    $design += @'");end=p.index("'@",start)+2
p=p[:start]+"""    $design += @'

## Oral detail review - 12 November 2026

v33 adds simplified upper/lower dental crowns and a tongue. The forms are artistic approximations because the available portrait shows a closed mouth. The tongue fits inside the dental arch, with zero pairwise tooth/tongue triangle intersections in seven checked poses. New anatomy remains hidden in the neutral frontal check. Existing face shape, materials, textures and expression buffers are unchanged. No image was uploaded or generated. The mouth interior still needs individualized anatomy and finer contour refinement.

Evidence, limitations and five-mesh animation contract: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v33_oral_review]].

'@"""+p[end:]
Path('work/archive33.ps1').write_text(p)
