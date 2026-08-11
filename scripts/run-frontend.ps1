$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

npm --prefix "$projectRoot\frontend" run dev
exit $LASTEXITCODE

