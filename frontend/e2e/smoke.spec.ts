import { test, expect } from "@playwright/test";
test("public shell renders", async ({ page }) => { await page.goto("/"); await expect(page).toHaveTitle(/CareerPilot AI/); });
test("opportunities route exists", async ({ page }) => { await page.goto("/opportunities"); await expect(page.getByRole("heading", {name:/Live opportunities/i})).toBeVisible(); });
