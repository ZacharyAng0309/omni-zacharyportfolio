$ErrorActionPreference = 'Stop'
$localRoot = 'C:\Users\ziyan\Documents\Codex\2026-10-30\acc'
$projectRoot = 'D:\omni-workstation\projects\ZacharyPortfolio'
$archiveRoot = "$projectRoot\artifacts\avatar-v32-codex-20261109"
$notePath = 'D:\omni-workstation\vault\01_Wiki\Projects\ZacharyPortfolio\07_Documentation\avatar_v32_mouth_review.md'
$record = Get-Content -LiteralPath "$localRoot\work\avatar-latest.json" -Raw | ConvertFrom-Json
$current = Get-Content -LiteralPath "$projectRoot\avatar-latest.json" -Raw | ConvertFrom-Json
if ($current.latest_verified_review_version -ne 'v31') { throw 'Shared latest record changed; re-read before updating.' }
if ((Test-Path -LiteralPath $archiveRoot) -or (Test-Path -LiteralPath $notePath)) { throw 'Milestone already exists; preserve immutable archive.' }
$validation = Get-Content -LiteralPath "$localRoot\work\mouth32-validation.json" -Raw | ConvertFrom-Json
$blendValidation = Get-Content -LiteralPath "$localRoot\work\blend32-validation.json" -Raw | ConvertFrom-Json
if ($validation.checks_failed -ne 0 -or $blendValidation.morph_meshes_synchronized -ne 2) { throw 'Verification incomplete.' }
foreach ($property in $record.files.PSObject.Properties) {
    $actual = (Get-FileHash -LiteralPath (Join-Path "$localRoot\outputs" $property.Name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $property.Value.sha256) { throw "Local file changed: $($property.Name)" }
}
$names = @('zachary_character_v32_candidate.glb','Zachary_Avatar_v32_Review.blend','avatar-v32-pose-targets.json','Avatar-v32-Review.md','avatar-v32-mouth-review.jpg','full32-front.png','full32-audit.json')
$files = $names | ForEach-Object { Get-Item -LiteralPath (Join-Path "$localRoot\outputs" $_) }
New-Item -ItemType Directory -Path "$archiveRoot\outputs", "$archiveRoot\work" | Out-Null
$files | Copy-Item -Destination "$archiveRoot\outputs"
Copy-Item -LiteralPath "$localRoot\outputs\zachary_character_v31_candidate.glb" -Destination "$archiveRoot\outputs"
Get-ChildItem -LiteralPath "$localRoot\work" -File | Where-Object { $_.Name -match '32' -and $_.Name -notmatch 'attempt1' -and $_.Extension -ne '.blend1' } | Copy-Item -Destination "$archiveRoot\work"
Copy-Item -LiteralPath "$localRoot\work\glb_asset.py", "$localRoot\work\kinematics27.py", "$localRoot\work\poses27.json" -Destination "$archiveRoot\work"
Copy-Item -LiteralPath "$projectRoot\src\graphics\SceneController.ts" -Destination "$archiveRoot\work\SceneController-at-review.ts"
$manifest = foreach ($file in $files) {
    $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    $destinationHash = (Get-FileHash -LiteralPath (Join-Path "$archiveRoot\outputs" $file.Name) -Algorithm SHA256).Hash
    if ($sourceHash -ne $destinationHash) { throw "Copy mismatch: $($file.Name)" }
    [pscustomobject]@{name=$file.Name; bytes=$file.Length; sha256=$sourceHash; verified=$true}
}
$manifest | ConvertTo-Json | Set-Content -LiteralPath "$archiveRoot\manifest.json" -Encoding utf8
$manifest | ConvertTo-Json | Set-Content -LiteralPath "$localRoot\work\archive32-validation.json" -Encoding utf8
$frontmatter = @'
---
id: DOC-ZacharyPortfolio-Avatar-v32-Mouth
title: Avatar mouth opening and oral cavity review
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, rig, face, review]
created_at: 2026-11-09
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'@
$body = Get-Content -LiteralPath "$localRoot\outputs\Avatar-v32-Review.md" -Raw -Encoding utf8
[IO.File]::WriteAllText($notePath, $frontmatter + [Environment]::NewLine + $body, [Text.UTF8Encoding]::new($false))
$indexPath = 'D:\omni-workstation\vault\01_Wiki\Projects\ZacharyPortfolio\07_Documentation\index.md'
$index = Get-Content -LiteralPath $indexPath -Raw -Encoding utf8
if (-not $index.Contains('avatar_v32_mouth_review')) {
    $index += "`n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v32_mouth_review|Avatar v32 Mouth Structure Review]]`n"
    [IO.File]::WriteAllText($indexPath, $index, [Text.UTF8Encoding]::new($false))
}
$designPath = 'D:\omni-workstation\vault\01_Wiki\Projects\ZacharyPortfolio\03_Design\persona_biometrics_and_likeness.md'
$design = Get-Content -LiteralPath $designPath -Raw -Encoding utf8
if (-not $design.Contains('Mouth structure review - 9 November 2026')) {
    $design += @'

## Mouth structure review - 9 November 2026

v32 replaces the closed speech surface with a rounded lip aperture and recessed cavity. Nominal neutral gap: 0.4 mm; half-width: 25 mm; cavity back: glTF Z 0.060 m. These are art-directed construction parameters, not measured biometrics. The closed-mouth reference does not establish teeth, tongue or open-mouth anatomy. No new facial textures were generated or uploaded. The mouthOpen, jawOpen and viseme_aa targets now open the cavity, with softened lip-corner movement. Teeth/tongue and finer lip/cheek deformation remain unfinished.

Evidence and integration contract: [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v32_mouth_review]].

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
Write-Output "Archived $($files.Count) deliverables, verified hashes, and updated the shared latest-version and Vault records to v32."
