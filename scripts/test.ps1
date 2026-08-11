$ErrorActionPreference = "Stop"

Push-Location backend
uv run pytest
$backendExitCode = $LASTEXITCODE
Pop-Location
if ($backendExitCode -ne 0) { exit $backendExitCode }

npm --prefix frontend run test
exit $LASTEXITCODE

