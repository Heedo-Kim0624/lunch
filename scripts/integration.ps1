$ErrorActionPreference = "Stop"

Push-Location backend
uv run pytest recommendations/tests/test_api.py
$exitCode = $LASTEXITCODE
Pop-Location
exit $exitCode

