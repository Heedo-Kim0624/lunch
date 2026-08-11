param(
    [switch]$Postgres
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

if ($Postgres) {
    $env:POSTGRES_DB = "lunch"
    $env:POSTGRES_USER = "lunch"
    $env:POSTGRES_PASSWORD = "lunch-local-only"
    $env:POSTGRES_HOST = "127.0.0.1"
    $env:POSTGRES_PORT = "5433"
}

Push-Location "$projectRoot\backend"
uv run python manage.py runserver 127.0.0.1:8000
$exitCode = $LASTEXITCODE
Pop-Location
exit $exitCode

