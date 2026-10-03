$ErrorActionPreference = "Stop"

function Assert-Pass {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        Write-Host "FAIL: $Message" -ForegroundColor Red
        exit 1
    }

    Write-Host "PASS: $Message" -ForegroundColor Green
}

Write-Host ""
Write-Host "==============================================="
Write-Host " CAREERPILOT AI - WEEK 7 FINAL GATE"
Write-Host "==============================================="
Write-Host ""

$root = Get-Location

# ------------------------------------------------
# 1. Branch identity
# ------------------------------------------------

$branch = (git branch --show-current).Trim()

Assert-Pass `
    ($branch -eq "week7-finalization") `
    "Running on week7-finalization branch"

# ------------------------------------------------
# 2. Audit tracker structural + completion gate
# ------------------------------------------------

Assert-Pass `
    (Test-Path ".\verify_week7_tracker.py") `
    "Audit tracker verifier exists"

python ".\verify_week7_tracker.py"

$tracker = Import-Csv ".\WEEK7_AUDIT_TRACKER.csv"

Assert-Pass `
    (@($tracker).Count -eq 1000) `
    "Exactly 1000 audit records exist"

$verified = @(
    $tracker |
    Where-Object { $_.Status -eq "VERIFIED" }
).Count

$unresolved = @(
    $tracker |
    Where-Object {
        $_.Status -in @("OPEN", "IN PROGRESS", "FIXED")
    }
).Count

Assert-Pass `
    ($verified -eq 1000) `
    "All 1000 audit items are VERIFIED"

Assert-Pass `
    ($unresolved -eq 0) `
    "No unresolved audit items remain"

foreach ($row in $tracker) {
    $item = $row.Item

    Assert-Pass `
        (-not [string]::IsNullOrWhiteSpace($row.FixCommit)) `
        "Audit item $item has FixCommit"

    Assert-Pass `
        (-not [string]::IsNullOrWhiteSpace($row.Evidence)) `
        "Audit item $item has Evidence"

    Assert-Pass `
        (-not [string]::IsNullOrWhiteSpace($row.VerifiedAt)) `
        "Audit item $item has VerifiedAt"

    Assert-Pass `
        (-not [string]::IsNullOrWhiteSpace($row.Verifier)) `
        "Audit item $item has Verifier"
}

# ------------------------------------------------
# 3. Backend compilation
# ------------------------------------------------

$env:PYTHONPATH = "."
$env:LLM_PROVIDER = "none"

python -m compileall backend

Assert-Pass `
    ($LASTEXITCODE -eq 0) `
    "Backend compileall passes"

# ------------------------------------------------
# 4. Full backend test suite
# ------------------------------------------------

python -m pytest -q

Assert-Pass `
    ($LASTEXITCODE -eq 0) `
    "Full backend pytest suite passes"

# ------------------------------------------------
# 5. Provider registry invariants
# ------------------------------------------------

$providerCheck = python -c "from backend.data.provider_catalog import build_provider_catalog; d=build_provider_catalog(128); print(len(d)); print(len({x.name for x in d}))"

$providerLines = @($providerCheck)

Assert-Pass `
    ($providerLines.Count -ge 2) `
    "Provider registry check returned results"

$catalogCount = [int]$providerLines[0]
$uniqueCount = [int]$providerLines[1]

Assert-Pass `
    ($catalogCount -eq 128) `
    "Provider catalog contains 128 definitions"

Assert-Pass `
    ($uniqueCount -eq 128) `
    "All provider names are unique"

# ------------------------------------------------
# 6. Frontend TypeScript
# ------------------------------------------------

Push-Location ".\frontend"

npx tsc --noEmit

Assert-Pass `
    ($LASTEXITCODE -eq 0) `
    "Frontend TypeScript check passes"

# ------------------------------------------------
# 7. Frontend production build
# ------------------------------------------------

npm run build

Assert-Pass `
    ($LASTEXITCODE -eq 0) `
    "Frontend production build passes"

Pop-Location

# ------------------------------------------------
# FINAL RESULT
# ------------------------------------------------

Write-Host ""
Write-Host "==============================================="
Write-Host " WEEK 7 FINAL GATE: PASSED"
Write-Host "==============================================="
Write-Host ""
Write-Host "1000/1000 audit items verified."
Write-Host "Backend tests passed."
Write-Host "Backend compilation passed."
Write-Host "Provider registry passed."
Write-Host "Frontend typecheck passed."
Write-Host "Frontend production build passed."
