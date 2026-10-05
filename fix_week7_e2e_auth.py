from pathlib import Path

path = Path('frontend/e2e/smoke.spec.ts')
expected = '''import { test, expect } from "@playwright/test";\ntest("public shell renders", async ({ page }) => { await page.goto("/"); await expect(page).toHaveTitle(/CareerPilot AI/); });\ntest("opportunities route exists", async ({ page }) => { await page.goto("/opportunities"); await expect(page.getByRole("heading", {name:/Live opportunities/i})).toBeVisible(); });\n'''
replacement = '''import { test, expect } from "@playwright/test";

test("public shell renders", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveTitle(/CareerPilot AI/);
});

test("protected opportunities route redirects unauthenticated users", async ({ page }) => {
  await page.goto("/opportunities", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(/\/auth\\?next=%2Fopportunities/);
  await expect(
    page.getByRole("heading", { name: /career operating system/i }),
  ).toBeVisible({ timeout: 15000 });
});

test("opportunities route renders for an authenticated session", async ({ page, context }) => {
  await context.addCookies([
    {
      name: "careerpilot_session",
      value: "e2e-smoke-session",
      domain: "127.0.0.1",
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);

  await page.goto("/opportunities", { waitUntil: "domcontentloaded" });
  await expect(
    page.getByRole("heading", { name: /Live opportunities/i }),
  ).toBeVisible({ timeout: 15000 });
});
'''
current = path.read_text(encoding='utf-8')
if current == replacement:
    print('SKIP frontend/e2e/smoke.spec.ts: already patched')
else:
    path.write_text(replacement, encoding='utf-8')
    print('PATCH frontend/e2e/smoke.spec.ts: auth-aware Week 7 E2E smoke suite')
