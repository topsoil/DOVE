$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "DOVE's virtual environment is not installed." -ForegroundColor Yellow
    Write-Host "Run: python -m venv .venv"
    Write-Host 'Then: .\.venv\Scripts\python.exe -m pip install -e ".[app,dev]"'
    exit 1
}

$Listener = Get-NetTCPConnection -LocalPort 8510 -State Listen -ErrorAction SilentlyContinue
if ($Listener) {
    Write-Host "Port 8510 is already in use. DOVE will not stop or replace that app." -ForegroundColor Yellow
    Write-Host "If DOVEboard is already running, open http://localhost:8510"
    exit 1
}

Write-Host "Starting DOVEboard at http://localhost:8510" -ForegroundColor Green
Write-Host "Research Memory Studio on port 8501 will not be changed."
& $Python -m streamlit run "app\streamlit_app.py" --server.port 8510 --server.address localhost

