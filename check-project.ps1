$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Project environment missing. Run setup-project.ps1 first."
}

Push-Location $projectRoot
try {
    Write-Host "Running project tests..."
    & $pythonPath -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) {
        throw "Project tests failed."
    }

    Write-Host "Checking API startup..."
    & $pythonPath -c "from ai_intraday_trading.main import app; assert app is not None; print('API startup: OK')"
    if ($LASTEXITCODE -ne 0) {
        throw "API startup check failed."
    }

    Write-Host "Project readiness: OK"
    Write-Host "Dhan MCP is configured separately in Codex and must be checked before live market actions."
}
finally {
    Pop-Location
}
