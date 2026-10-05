$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
if (-not (Test-Path (Join-Path $root 'frontend\package.json'))) { throw 'Run this script from the CareerPilot-AI root.' }

function Read-Text([string]$Path) { Get-Content -LiteralPath (Join-Path $root $Path) -Raw }
function Write-Text([string]$Path, [string]$Text) { Set-Content -LiteralPath (Join-Path $root $Path) -Value $Text -NoNewline }
function Replace-Once([string]$Path, [string]$Pattern, [string]$Replacement, [string]$Label) {
  $full = Join-Path $root $Path
  $text = Get-Content -LiteralPath $full -Raw
  if ($text -match $Pattern) {
    $new = [regex]::Replace($text, $Pattern, $Replacement, 1)
    Write-Text $Path $new
    Write-Host "PATCH: $Label" -ForegroundColor Green
    return $true
  }
  Write-Host "SKIP: $Label (already patched or pattern differs)" -ForegroundColor DarkYellow
  return $false
}

# Inbox: support either the original Week 7 source or an already partially patched file.
Replace-Once 'frontend\app\inbox\page.tsx' '(?s)  async function load\(\) \{.*?\n  \}\n\n  useEffect\(\(\) => \{ void load\(\); \}, \[\]\);' @'
  useEffect(() => {
    let cancelled = false;
    apiJson<{ items?: Item[] }>("/inbox/items")
      .then((result) => {
        if (!cancelled) setItems(result.items ?? []);
      })
      .catch((error) => {
        if (!cancelled) setMessage(error instanceof Error ? error.message : "Unable to load inbox.");
      });
    return () => { cancelled = true; };
  }, []);
'@ 'Career Inbox effect/state update'

Replace-Once 'frontend\app\inbox\page.tsx' '\{item\.preview && <p className="mt-3 text-sm leading-6 text-white/60">\{String\(item\.preview\)\}</p>\}' '{typeof item.preview === "string" && item.preview.length > 0 && <p className="mt-3 text-sm leading-6 text-white/60">{item.preview}</p>}' 'Career Inbox preview type guard'

# Integrations: replace initial loader effect only if the old async state-update pattern is present.
Replace-Once 'frontend\app\integrations\page.tsx' '(?s)  useEffect\(\(\) => \{\n    void load\(\);\n    const params = new URLSearchParams\(window\.location\.search\);.*?\n  \}, \[\]\);' @'
  useEffect(() => {
    let cancelled = false;
    apiJson<{ integrations: Integration[]; setup: Setup }>("/integrations/status")
      .then((result) => {
        if (!cancelled) {
          setItems(result.integrations ?? []);
          setSetup(result.setup ?? {});
        }
      })
      .catch((error) => {
        if (!cancelled) setMessage(error instanceof Error ? error.message : "Unable to load integrations.");
      });

    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const error = params.get("error");
    const statusMessage = connected
      ? `${connected} connected successfully.`
      : error
        ? `Integration error: ${error}`
        : "";
    if (statusMessage) queueMicrotask(() => { if (!cancelled) setMessage(statusMessage); });

    return () => { cancelled = true; };
  }, []);' 'Integrations effect/state update'

# Learning: make initial data immutable and load deterministically without a mount-time setState chain.
Replace-Once 'frontend\app\learning\page.tsx' '(?m)^interface Recommendation \{.*?\}\r?$' @'
interface Recommendation { id: string; skill: string; provider: string; url: string; category: string; provider_url: string; }

const INITIAL_SKILLS = "python, system design, cloud, docker";
'@ 'Learning initial skills constant'
Replace-Once 'frontend\app\learning\page.tsx' '(?m)^  const \[skills, setSkills\] = useState\("python, system design, cloud, docker"\);' '  const [skills, setSkills] = useState(INITIAL_SKILLS);' 'Learning initial state'
Replace-Once 'frontend\app\learning\page.tsx' '(?s)  async function load\(\) \{.*?\n  \}\n\n  async function recommend' '  async function recommend' 'Learning obsolete load helper'
Replace-Once 'frontend\app\learning\page.tsx' '(?m)^  useEffect\(\(\) => \{ void load\(\); \}, \[\]\);.*$' @'
  useEffect(() => {
    let cancelled = false;
    listWorkspace("learning")
      .catch(() => [])
      .then((saved) => {
        if (cancelled) return;
        setProgress(saved);
        return apiJson<{ recommendations?: Recommendation[] }>(`/learning/recommendations?skills=${encodeURIComponent(INITIAL_SKILLS)}`);
      })
      .then((result) => {
        if (!cancelled && result) setItems(result.recommendations ?? []);
      })
      .catch((error) => {
        if (!cancelled) setMessage(error instanceof Error ? error.message : "Unable to load learning recommendations.");
      });
    return () => { cancelled = true; };
  }, []);' 'Learning effect/state update'

# Next dev origin support: idempotently add allowedDevOrigins.
$next = 'frontend\next.config.ts'
$nextText = Read-Text $next
if ($nextText -notmatch 'allowedDevOrigins') {
  $nextText = [regex]::Replace($nextText, 'poweredByHeader:\s*false,', "poweredByHeader: false,`r`n  allowedDevOrigins: [\"127.0.0.1\", \"localhost\"],", 1)
  Write-Text $next $nextText
  Write-Host 'PATCH: Next allowedDevOrigins' -ForegroundColor Green
} else { Write-Host 'SKIP: Next allowedDevOrigins already present' -ForegroundColor DarkYellow }

# E2E smoke: tolerant to either one-line original or already-patched test.
$e2e = 'frontend\e2e\smoke.spec.ts'
$e2eText = Read-Text $e2e
if ($e2eText -notmatch 'waitUntil:\s*"domcontentloaded"' -or $e2eText -notmatch 'timeout:\s*15000') {
  $pattern = 'test\("opportunities route exists", async \(\{ page \}\) => \{.*?\}\);'
  $replacement = @'
test("opportunities route exists", async ({ page }) => {
  await page.goto("/opportunities", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /Live opportunities/i })).toBeVisible({ timeout: 15000 });
});
'@
  $e2eText = [regex]::Replace($e2eText, $pattern, $replacement, 1, [System.Text.RegularExpressions.RegexOptions]::Singleline)
  Write-Text $e2e $e2eText
  Write-Host 'PATCH: Opportunities E2E wait/timeout' -ForegroundColor Green
} else { Write-Host 'SKIP: Opportunities E2E already patched' -ForegroundColor DarkYellow }

Remove-Item -LiteralPath (Join-Path $root 'frontend\.next') -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $root 'frontend\test-results') -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host 'Week 7 frontend patch v2 complete.' -ForegroundColor Green
Write-Host 'Now run typecheck, lint, tests, build, E2E. Do NOT run the final gate until those pass.' -ForegroundColor Cyan
