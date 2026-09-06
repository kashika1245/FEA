import { expect, test } from "@playwright/test";

test.describe("Paper A observatory", () => {
  test("overview reflects live API provenance", async ({ page }) => {
    const failed: string[] = [];
    page.on("pageerror", (error) => failed.push(error.message));
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /how far can a structural surrogate/i })).toBeVisible();
    await expect(page.getByRole("row", { name: /Variable-wise observations/ })).toContainText(/132/);
    expect(failed).toEqual([]);
  });

  test("experiments and detail load", async ({ page }) => {
    await page.goto("/experiments");
    await expect(page.getByRole("link", { name: "paper-a.phase2.v1" })).toBeVisible();
    await page.getByRole("link", { name: "paper-a.phase2.v1" }).click();
    await expect(page.getByRole("heading", { name: "paper-a.phase2.v1" })).toBeVisible();
    await expect(page.getByText(/immutable/i)).toBeVisible();
  });

  test("research pages load stored artefacts", async ({ page }) => {
    await page.goto("/profiles?experiment=paper-a.phase2.v1");
    await expect(page.getByText(/research\/profiles/i)).toBeVisible();
    await page.goto("/thresholds?experiment=paper-a.phase2.v1");
    await expect(page.getByRole("columnheader", { name: "Lower 5%" })).toBeVisible();
    await page.goto("/asymmetry?experiment=paper-a.phase2.v1");
    await expect(page.getByRole("columnheader", { name: "Upper − lower" })).toBeVisible();
    await page.goto("/interpolation?experiment=paper-a.phase2.v1");
    await expect(page.getByText(/Competence gate passed|Gate notes/).first()).toBeVisible();
    await page.goto("/artifacts?experiment=paper-a.phase2.v1");
    await expect(page.getByText("manifest.json")).toBeVisible({ timeout: 15000 });
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("link", { name: "Download" }).first().click();
    const download = await downloadPromise;
    expect(download.suggestedFilename().length).toBeGreaterThan(0);
  });

  test("primary pages expose headings and labelled controls", async ({ page }) => {
    await page.goto("/profiles?experiment=paper-a.phase2.v1");
    await expect(page.getByRole("heading", { name: /variable-wise extrapolation profiles/i })).toBeVisible();
    await expect(page.getByLabel("Variable")).toBeVisible();
    await expect(page.getByLabel("Seed")).toBeVisible();
    await page.goto("/methodology");
    await expect(page.getByRole("heading", { name: /limitations/i })).toBeVisible();
    await expect(page.getByText(/A3\+F is one combined-variable experiment/i)).toBeVisible();
  });

  test("404 page and combined page render", async ({ page }) => {
    await page.goto("/not-a-route");
    await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
    await page.goto("/combined?experiment=paper-a.phase2.v1");
    await expect(page.getByRole("heading", { name: /combined a3/i })).toBeVisible();
  });

  test("jobs page can launch a real tiny experiment", async ({ page }) => {
    await page.goto("/jobs");
    await page.getByRole("button", { name: /launch tiny phase 2 pipeline/i }).click();
    await expect(page.getByRole("link", { name: /paper-a\.phase3\.tiny-/ }).first()).toBeVisible({
      timeout: 30000,
    });
    await expect(page.getByText(/queued|running|completed/i).first()).toBeVisible();
  });
});
