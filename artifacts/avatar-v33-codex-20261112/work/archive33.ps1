$ErrorActionPreference = 'Stop'
$localRoot = 'C:\Users\ziyan\Documents\Codex\2026-10-30\acc'
$projectRoot = 'D:\omni-workstation\projects\ZacharyPortfolio'
$archiveRoot = "$projectRoot\artifacts\avatar-v33-codex-20261112"
$notePath = 'D:\omni-workstation\vault\01_Wiki\Projects\ZacharyPortfolio\07_Documentation\avatar_v33_oral_review.md'
$record = Get-Content -LiteralPath "$localRoot\work\avatar-latest.json" -Raw | ConvertFrom-Json
$current = Get-Content -LiteralPath "$projectRoot\avatar-latest.json" -Raw | ConvertFrom-Json
if ($current.latest_verified_review_version -ne 'v32') { throw 'Shared latest record changed; re-read before updating.' }
if ((Test-Path -LiteralPath $archiveRoot) -or (Test-Path -LiteralPath $notePath)) { throw 'Milestone already exists; preserve immutable archive.' }
$validation = Get-Content -LiteralPath "$localRoot\work\oral33-validation.json" -Raw | ConvertFrom-Json
$blendValidation = Get-Content -LiteralPath "$localRoot\work\blend33-validation.json" -Raw | ConvertFrom-Json
if ($validation.checks_failed -ne 0 -or $blendValidation.morph_meshes_synchronized -ne 5) { throw 'Verification incomplete.' }
foreach ($property in $record.files.PSObject.Properties) {
    $actual = (Get-FileHash -LiteralPath (Join-Path "$localRoot\outputs" $property.Name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $property.Value.sha256) { throw "Local file changed: $($property.Name)" }
}
$names = @('zachary_character_v33_candidate.glb','Zachary_Avatar_v33_Review.blend','avatar-v33-pose-targets.json','Avatar-v33-Review.md','avatar-v33-mouth-review.jpg','avatar-v33-oral-cutaway.png','full33-front.png','full33-audit.json')
$files = $names | ForEach-Object { Get-Item -LiteralPath (Join-Path "$localRoot\outputs" $_) }
New-Item -ItemType Directory -Path "$archiveRoot\outputs", "$archiveRoot\work" | Out-Null
$files | Copy-Item -Destination "$archiveRoot\outputs"
Copy-Item -LiteralPath "$localRoot\outputs\zachary_character_v32_candidate.glb" -Destination "$archiveRoot\outputs"
Get-ChildItem -LiteralPath "$localRoot\work" -File | Where-Object { $_.Name -match '33' -and $_.Name -notmatch 'attempt1' -and $_.Extension -ne '.blend1' } | Copy-Item -Destination "$archiveRoot\work"
Copy-Item -LiteralPath "$localRoot\work\glb_asset.py", "$localRoot\work\kinematics27.py", "$localRoot\work\poses27.json" -Destination "$archiveRoot\work"
Copy-Item -LiteralPath "$projectRoot\src\graphics\SceneController.ts" -Destination "$archiveRoot\work\SceneController-at-review.ts"
$manifest = foreach ($file in $files) {
    $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    $destinationHash = (Get-FileHash -LiteralPath (Join-Path "$archiveRoot\outputs" $file.Name) -Algorithm SHA256).Hash
    if ($sourceHash -ne $destinationHash) { throw "Copy mismatch: $($file.Name)" }
    [pscustomobject]@{name=$file.Name; bytes=$file.Length; sha256=$sourceHash; verified=$true}
}
$manifest | ConvertTo-Json | Set-Content -LiteralPath "$archiveRoot\manifest.json" -Encoding utf8
$manifest | ConvertTo-Json | Set-Content -LiteralPath "$localRoot\work\archive33-validation.json" -Encoding utf8
$frontmatter = @'
---
id: DOC-ZacharyPortfolio-Avatar-v33-Oral
title: Avatar oral detail and clearance review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, rig, face, review]
created_at: 2026-11-12
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'@
$body = Get-Content -LiteralPath "$localRoot\outputs\Avatar-v33-Review.md" -Raw -Encoding utf8
[IO.File]::WriteAllText($notePath, $frontmatter + [Environment]::NewLine + $body, [Text.UTF8Encoding]::new($false))
$indexPath = 'D:\omni-workstation\vault\01_Wiki\Projects\ZacharyPortfolio\07_Documentation\index.md'
$index = Get-Content -LiteralPath $indexPath -Raw -Encoding utf8
if (-not $index.Contains('avatar_v33_oral_review')) {
    $index += "`n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v33_oral_review|Avatar v33 Oral Detail Review]]`n"
    [IO.File]::WriteAllText($indexPath, $index, [Text.UTF8Encoding]::new($false))
}
$designPath = 'D:\omni-workstation\vault\01_Wiki\Projects\ZacharyPortfolio\03_Design\persona_biometrics_and_likeness.md'
$design = Get-Content -LiteralPath $designPath -Raw -Encoding utf8
if (-not $design.Contains('Oral detail review - 12 November 2026')) {
    $design += @'

## Oral detail review - 12 November 2026

v33 adds simplified upper/lower dental crowns and a tongue. The forms are artistic approximations because the available portrait shows a closed mouth. The tongue fits inside the dental arch, with zero pairwise tooth/tongue triangle intersections in seven checked poses. New anatomy remains hidden in the neutral frontal check. Existing face shape, materials, textures and expression buffers are unchanged. No image was uploaded or generated. The mouth interior still needs individualized anatomy and finer contour refinement.

Evidence, limitations and five-mesh animation contract: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v33_oral_review]].

'@
    [IO.File]::WriteAllText($designPath, $design, [Text.UTF8Encoding]::new($false))
}
Copy-Item -LiteralPath "$localRoot\work\AVATAR_LATEST.md", "$localRoot\work\avatar-latest.json" -Destination $archiveRoot
Copy-Item -LiteralPath "$localRoot\work\AVATAR_LATEST.md", "$localRoot\work\avatar-latest.json" -Destination $projectRoot
$saved = Get-Content -LiteralPath "$projectRoot\avatar-latest.json" -Raw | ConvertFrom-Json
foreach ($property in $saved.files.PSObject.Properties) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $projectRoot $property.Value.path) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $property.Value.sha256) { throw "Latest record mismatch: $($property.Name)" }
}
Write-Output "Archived $($files.Count) deliverables, verified hashes, and updated the shared latest-version and Vault records to v33."
