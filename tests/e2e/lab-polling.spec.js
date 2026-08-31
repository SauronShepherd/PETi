import { test, expect } from "@playwright/test";

test("real adapter polling is non-overlapping and pauses while hidden", async ({ page, request }) => {
  const fixture = await (await request.get("/demo/lab/data.json")).json();
  await page.goto("/#HOME");
  await page.evaluate(async (data) => {
    history.replaceState({}, "", "/#ADMIN/COMMAND_CENTER");
    document.body.innerHTML = '<div id="peti-lab-root"></div>';
    window.PETI_LAB_POLL_INTERVALS = {runs:40, command:40};
    window.__labPoll = {overview:0, active:0, maxActive:0};
    window.PETI_API = async (path) => {
      window.__labPoll.active += 1;
      window.__labPoll.maxActive = Math.max(window.__labPoll.maxActive, window.__labPoll.active);
      if (path.endsWith("/overview")) window.__labPoll.overview += 1;
      await new Promise((resolve) => setTimeout(resolve, 15));
      window.__labPoll.active -= 1;
      if (path.endsWith("/access")) return {can_view_lab:true};
      if (path.includes("/runs?")) return {items:data.runs};
      if (path.endsWith("/agents")) return {items:data.agents};
      if (path.endsWith("/models")) return {items:data.models};
      if (path.includes("/feedback?")) return {items:data.feedback};
      if (path.endsWith("/evidence/metrics")) return data.evidence;
      if (path.endsWith("/safety/reviews")) return data.safety;
      if (path.endsWith("/performance")) return data.performance;
      if (path.endsWith("/health")) return data.health;
      if (path.endsWith("/audit")) return {items:[]};
      if (path.endsWith("/overview")) return data.overview;
      throw new Error(`Unexpected ${path}`);
    };
    const {mountLab} = await import(`/lab/lab.js?poll-test=${Date.now()}`);
    await mountLab();
    window.__labPoll.maxActive = window.__labPoll.active;
  }, fixture);
  await expect(page.getByRole("heading", {name:"Multi-Agent Mission Control"})).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.__labPoll.overview)).toBeGreaterThan(1);
  expect(await page.evaluate(() => window.__labPoll.maxActive)).toBeLessThanOrEqual(2);

  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", {configurable:true, get:() => true});
    document.dispatchEvent(new Event("visibilitychange"));
  });
  const pausedAt = await page.evaluate(() => window.__labPoll.overview);
  await page.waitForTimeout(160);
  expect(await page.evaluate(() => window.__labPoll.overview)).toBe(pausedAt);

  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", {configurable:true, get:() => false});
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect.poll(() => page.evaluate(() => window.__labPoll.overview)).toBeGreaterThan(pausedAt);
});
