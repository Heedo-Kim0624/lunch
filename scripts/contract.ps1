$ErrorActionPreference = "Stop"

Push-Location backend
uv run python manage.py check
$exitCode = $LASTEXITCODE
Pop-Location
exit $exitCode

