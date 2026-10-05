$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
if (-not (Test-Path (Join-Path $root 'frontend\package.json'))) {
    throw 'Run this script from the CareerPilot-AI root.'
}

function Replace-Exact([string]$Path, [string]$Old, [string]$New) {
    $full = Join-Path $root $Path
    $text = Get-Content -LiteralPath $full -Raw
    if (-not $text.Contains($Old)) {
        throw "Expected source pattern not found in $Path. The file may already be patched or differs from the Week 7 FINAL package."
    }
    Set-Content -LiteralPath $full -Value ($text.Replace($Old, $New)) -NoNewline
}

Replace-Exact 'frontend\app\inbox\page.tsx' @'
  async function load() {
    try { const result = await apiJson<{ items?: Item[] }>("/inbox/items"); setItems(result.items ?? []); } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to load inbox."); }
  }

  useEffect(() => { void load(); }, []);
'@ @'
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
'@

Replace-Exact 'frontend\app\inbox\page.tsx' '{item.preview && <p className="mt-3 text-sm leading-6 text-white/60">{String(item.preview)}</p>}' '{typeof item.preview === "string" && item.preview.length > 0 && <p className="mt-3 text-sm leading-6 text-white/60">{item.preview}</p>}'

Replace-Exact 'frontend\app\integrations\page.tsx' @'
  useEffect(() => {
    void load();
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const error = params.get("error");
    if (connected) setMessage(`${connected} connected successfully.`);
    if (error) setMessage(`Integration error: ${error}`);
  }, []);
'@ @'
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
  }, []);
'@

Replace-Exact 'frontend\app\learning\page.tsx' 'interface Recommendation { id: string; skill: string; provider: string; url: string; category: string; provider_url: string; }' 'interface Recommendation { id: string; skill: string; provider: string; url: string; category: string; provider_url: string; }`r`n`r`nconst INITIAL_SKILLS = "python, system design, cloud, docker";'
Replace-Exact 'frontend\app\learning\page.tsx' '  const [skills, setSkills] = useState("python, system design, cloud, docker");' '  const [skills, setSkills] = useState(INITIAL_SKILLS);'
Replace-Exact 'frontend\app\learning\page.tsx' @'
  async function load() {
    const saved = await listWorkspace("learning").catch(() => []);
    setProgress(saved);
    await recommend();
  }

'@ ''
Replace-Exact 'frontend\app\learning\page.tsx' '  useEffect(() => { void load(); }, []); // intentionally once on page load' @'
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
  }, []);
'@

Replace-Exact 'frontend\next.config.ts' '  poweredByHeader: false,`r`n' '  poweredByHeader: false,`r`n  allowedDevOrigins: ["127.0.0.1", "localhost"],`r`n'

Replace-Exact 'frontend\e2e\smoke.spec.ts' 'test("opportunities route exists", async ({ page }) => { await page.goto("/opportunities"); await expect(page.getByRole("heading", {name:/Live opportunities/i})).toBeVisible(); });' @'
test("opportunities route exists", async ({ page }) => {
  await page.goto("/opportunities", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /Live opportunities/i })).toBeVisible({ timeout: 15000 });
});
'@

Remove-Item -LiteralPath (Join-Path $root 'frontend\.next') -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $root 'frontend\test-results') -Recurse -Force -ErrorAction SilentlyContinue

Write-Host 'Week 7 frontend fixes applied.' -ForegroundColor Green
Write-Host 'Next: run npm audit fix (without --force), then typecheck, lint, tests, build, E2E, and final gate.' -ForegroundColor Cyan
