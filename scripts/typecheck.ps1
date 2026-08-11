$ErrorActionPreference = "Stop"

Push-Location backend
uv run python manage.py check
$backendExitCode = $LASTEXITCODE
if ($backendExitCode -eq 0) {
    uv run python manage.py makemigrations --check --dry-run
    $backendExitCode = $LASTEXITCODE
}
Pop-Location
if ($backendExitCode -ne 0) { exit $backendExitCode }

npm --prefix frontend run typecheck
exit $LASTEXITCODE
