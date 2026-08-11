param(
    [switch]$Postgres
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

uv sync --project "$projectRoot\backend" --dev
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

npm --prefix "$projectRoot\frontend" install
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Postgres) {
    docker compose --project-directory $projectRoot up -d --wait db
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $env:POSTGRES_DB = "lunch"
    $env:POSTGRES_USER = "lunch"
    $env:POSTGRES_PASSWORD = "lunch-local-only"
    $env:POSTGRES_HOST = "127.0.0.1"
    $env:POSTGRES_PORT = "5433"
}

Push-Location "$projectRoot\backend"
uv run python manage.py migrate
if ($LASTEXITCODE -eq 0) {
    uv run python manage.py seed_foods
}
$backendExitCode = $LASTEXITCODE
Pop-Location

if ($backendExitCode -ne 0) { exit $backendExitCode }
Write-Host "Lunch Machine setup complete."

