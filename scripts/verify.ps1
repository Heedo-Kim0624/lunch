$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot

try {
    Write-Host "JARVIS V1.3 project verifier"
    if (-not (Test-Path ".\AGENTS.md")) { throw "AGENTS.md missing" }
    if (-not (Test-Path ".\docs\prd.md")) { throw "docs/prd.md missing" }
    if (-not (Test-Path ".\.jarvis\kanban.json")) { throw ".jarvis\kanban.json missing" }

    & ".\scripts\lint.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & ".\scripts\typecheck.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & ".\scripts\test.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    npm --prefix frontend run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "State: pass"
}
finally {
    Pop-Location
}

