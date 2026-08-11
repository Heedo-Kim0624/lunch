$ErrorActionPreference = "Stop"

Push-Location backend
uv run ruff check .
$backendExitCode = $LASTEXITCODE
Pop-Location
if ($backendExitCode -ne 0) { exit $backendExitCode }

npm --prefix frontend run lint
exit $LASTEXITCODE
