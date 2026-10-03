$ErrorActionPreference = "Stop"

function Invoke-Native {
    param([string]$Label,[string]$Command,[string[]]$Arguments)
    Write-Host $Label
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $Label (exit $LASTEXITCODE)" -ForegroundColor Red; exit $LASTEXITCODE }
}

Write-Host ""
Write-Host "==============================================="
Write-Host " CAREERPILOT AI - PHASE 2→5 LOCAL GATE"
Write-Host "==============================================="
Write-Host ""
Invoke-Native "[1/7] P0 authoritative verifier" "python" @(".\verify_phase1_p0.py")
Invoke-Native "[2/7] Phase 2→5 root-cause verifier" "python" @(".\verify_phase2_5.py")
$env:PYTHONPATH="."; $env:LLM_PROVIDER="none"
Invoke-Native "[3/7] Backend compilation" "python" @("-m","compileall","backend")
Invoke-Native "[4/7] Backend tests" "python" @("-m","pytest","-q")
Push-Location ".\frontend"
try {
  Invoke-Native "[5/7] Frontend dependency installation" "npm" @("install")
  Invoke-Native "[6/7a] Frontend typecheck" "npm" @("run","typecheck")
  Invoke-Native "[6/7b] Frontend lint" "npm" @("run","lint")
  Invoke-Native "[6/7c] Frontend tests" "npm" @("test")
  Invoke-Native "[7/7] Frontend production build" "npm" @("run","build")
} finally { Pop-Location }
Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host " PHASE 2→5 LOCAL GATE: PASSED" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
