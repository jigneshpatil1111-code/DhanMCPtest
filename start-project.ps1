$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Project environment missing. Run setup-project.ps1 first."
}

Push-Location $projectRoot
try {
    & $pythonPath -m uvicorn ai_intraday_trading.main:app --host 127.0.0.1 --port 8000
}
finally {
    Pop-Location
}
