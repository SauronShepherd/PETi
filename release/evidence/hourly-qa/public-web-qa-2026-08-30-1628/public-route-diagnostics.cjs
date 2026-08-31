const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const outDir = path.resolve('release/evidence/hourly-qa/public-web-qa-2026-08-30-1628/route-audit');
fs.mkdirSync(outDir, { recursive: true });
const target = 'https://peti-care.web.app/?demo=1';
const routes = ['HOME','SCAN','HISTORY','PROFILE','AGENTS','CARE','BODY_CHECK','RECORDS','ASSISTANT','PLANS','SETTINGS','FEEDBACK','COLLABORATION','LIBRARY','ADMIN'];
const viewports = {
  desktop: { width: 1440, height: 900, isMobile: false },
  tablet: { width: 1024, height: 768, isMobile: false },
  mobile: { width: 390, height: 844, isMobile: true },
};

(async () => {
  const browser = await chromium.launch();
  const results = [];
  for (const [viewportName, viewport] of Object.entries(viewports)) {
    const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, isMobile: viewport.isMobile });
    const page = await context.newPage();
    const consoleMessages = [];
    const failedRequests = [];
    page.on('console', msg => {
      if (['error', 'warning'].includes(msg.type())) consoleMessages.push({ type: msg.type(), text: msg.text(), url: page.url() });
    });
    page.on('requestfailed', req => failedRequests.push({ url: req.url(), method: req.method(), failure: req.failure()?.errorText || '' }));
    for (const route of routes) {
      const url = `${target}#${route}`;
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.waitForTimeout(300);
      const base = `${route.toLowerCase().replace(/_/g, '-')}-${viewportName}`;
      const screenshot = path.join(outDir, `${base}.png`);
      await page.screenshot({ path: screenshot, fullPage: true });
      const info = await page.evaluate((screenshotPath) => {
        const hiddenOrUnnamed = [...document.querySelectorAll('button, a, input, select, textarea')].map((el) => ({
          tag: el.tagName.toLowerCase(),
          text: (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim(),
          aria: el.getAttribute('aria-label') || '',
          id: el.id || '',
          disabled: !!el.disabled,
          rect: (() => { const r = el.getBoundingClientRect(); return { width: Math.round(r.width), height: Math.round(r.height) }; })(),
        })).filter((el) => !el.text && !el.aria);
        const bodyText = document.body.innerText;
        return {
          finalUrl: location.href,
          title: document.title,
          appVisible: !!document.querySelector('#app') && getComputedStyle(document.querySelector('#app')).display !== 'none',
          mainTitle: document.querySelector('.title')?.textContent?.trim() || '',
          overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          brokenImages: [...document.images].filter(img => !img.complete || img.naturalWidth === 0).map(img => img.currentSrc || img.src),
          focusables: [...document.querySelectorAll('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])')].length,
          unnamedControls: hiddenOrUnnamed,
          forbiddenText: ['TypeError','ReferenceError','FirebaseError','Traceback','apiKey','secret','token'].filter(t => bodyText.includes(t)),
          firstText: bodyText.replace(/\s+/g, ' ').trim().slice(0, 500),
          screenshot: screenshotPath,
        };
      }, screenshot);
      results.push({ viewport: viewportName, route, ...info });
    }
    await page.goto(`${target}#HOME`, { waitUntil: 'networkidle' });
    await page.goto(`${target}#SCAN`, { waitUntil: 'networkidle' });
    await page.reload({ waitUntil: 'networkidle' });
    const afterReload = page.url();
    await page.goBack({ waitUntil: 'networkidle' });
    const afterBack = page.url();
    await page.goForward({ waitUntil: 'networkidle' });
    const afterForward = page.url();
    results.push({ viewport: viewportName, route: 'NAVIGATION_FLOW', afterReload, afterBack, afterForward });
    await context.close();
    results.push({ viewport: viewportName, route: 'RUNTIME_MESSAGES', consoleMessages, failedRequests });
  }
  await browser.close();
  fs.writeFileSync(path.join(outDir, 'route-diagnostics.json'), JSON.stringify({ target, createdAt: new Date().toISOString(), results }, null, 2));
})();
