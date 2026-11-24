$ErrorActionPreference = 'Stop'
$localRoot = 'C:\Users\ziyan\Documents\Codex\2026-10-30\acc'
$projectRoot = 'D:\omni-workstation\projects\ZacharyPortfolio'
$archiveRoot = "$projectRoot\artifacts\avatar-v28-codex-20261104"
if (Test-Path -LiteralPath $archiveRoot) { throw 'Archive already exists; preserve immutable milestone.' }
New-Item -ItemType Directory -Path "$archiveRoot\outputs", "$archiveRoot\work" | Out-Null
$files = Get-ChildItem -LiteralPath "$localRoot\outputs" -File | Where-Object { $_.Name -match '28' -and $_.Extension -ne '.blend1' }
$files | Copy-Item -Destination "$archiveRoot\outputs"
Copy-Item -LiteralPath "$localRoot\outputs\zachary_character_v26_candidate.glb", "$localRoot\outputs\zachary_character_v27_candidate.glb", "$localRoot\outputs\Zachary_Avatar_v26_Review.blend" -Destination "$archiveRoot\outputs"
Get-ChildItem -LiteralPath "$localRoot\work" -File | Where-Object { $_.Name -match '28' -and $_.Extension -ne '.blend1' } | Copy-Item -Destination "$archiveRoot\work"
Copy-Item -LiteralPath "$localRoot\work\glb_asset.py", "$localRoot\work\kinematics27.py", "$localRoot\work\poses27.json" -Destination "$archiveRoot\work"
Get-ChildItem -LiteralPath "$localRoot\work" -Filter 'hand-v27-*.png' | Copy-Item -Destination "$archiveRoot\work"
Copy-Item -LiteralPath "$projectRoot\src\graphics\SceneController.ts" -Destination "$archiveRoot\work\SceneController-at-review.ts"
$notePath = 'D:\omni-workstation\vault\01_Wiki\Projects\ZacharyPortfolio\07_Documentation\avatar_v28_finger_review.md'
if (Test-Path -LiteralPath $notePath) { throw 'Review note already exists.' }
$frontmatter = @'
---
id: DOC-ZacharyPortfolio-Avatar-v28-Fingers
title: Avatar finger joint fitting and skin-weight refinement
type: documentation
stage: 07_Documentation
project: ZacharyPortfolio
status: draft
tags: [avatar, blender, rig, hands, review]
created_at: 2026-11-04
links:
  - "[[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/index]]"
---

'@
$body = Get-Content -LiteralPath "$localRoot\outputs\Avatar-v28-Review.md" -Raw
[IO.File]::WriteAllText($notePath, $frontmatter + [Environment]::NewLine + $body, [Text.UTF8Encoding]::new($false))
$indexPath = 'D:\omni-workstation\vault\01_Wiki\Projects\ZacharyPortfolio\07_Documentation\index.md'
$index = Get-Content -LiteralPath $indexPath -Raw
if (-not $index.Contains('avatar_v28_finger_review')) {
    $index += "`n   - [[01_Wiki/Projects/ZacharyPortfolio/07_Documentation/avatar_v28_finger_review|Avatar v28 Finger Articulation Review]]`n"
    [IO.File]::WriteAllText($indexPath, $index, [Text.UTF8Encoding]::new($false))
}
$manifest = foreach ($file in $files) {
    $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    $destinationHash = (Get-FileHash -LiteralPath (Join-Path "$archiveRoot\outputs" $file.Name) -Algorithm SHA256).Hash
    if ($sourceHash -ne $destinationHash) { throw "Copy mismatch: $($file.Name)" }
    [pscustomobject]@{name=$file.Name; bytes=$file.Length; sha256=$sourceHash; verified=$true}
}
$manifest | ConvertTo-Json | Set-Content -LiteralPath "$archiveRoot\manifest.json" -Encoding utf8
$manifest | ConvertTo-Json | Set-Content -LiteralPath "$localRoot\work\archive28-validation.json" -Encoding utf8
Copy-Item -LiteralPath "$localRoot\work\AVATAR_LATEST.md", "$localRoot\work\avatar-latest.json" -Destination $projectRoot
Copy-Item -LiteralPath "$localRoot\work\AVATAR_LATEST.md", "$localRoot\work\avatar-latest.json" -Destination $archiveRoot
$record = Get-Content -LiteralPath "$projectRoot\avatar-latest.json" -Raw | ConvertFrom-Json
foreach ($property in $record.files.PSObject.Properties) {
    $item = $property.Value
    $actual = (Get-FileHash -LiteralPath (Join-Path $projectRoot $item.path) -Algorithm SHA256).Hash
    if ($actual.ToLowerInvariant() -ne $item.sha256) { throw "Latest record mismatch: $($property.Name)" }
}
Write-Output "Archived $($files.Count) deliverables, verified hashes, and updated latest-version records to v28."
