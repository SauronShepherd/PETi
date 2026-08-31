const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const outDir = path.resolve('release/evidence/hourly-qa/public-web-qa-2026-08-30-1628/fresh-route-audit');
fs.mkdirSync(outDir, { recursive: true });
const target = 'https://peti-care.web.app/?demo=1';
const routes = ['HOME','SCAN','HISTORY','PROFILE','AGENTS','CARE','BODY_CHECK','RECORDS','ASSISTANT','PLANS','SETTINGS','FEEDBACK','COLLABORATION','LIBRARY','ADMIN'];
const viewports = { desktop: { width: 1440, height: 900, isMobile: false }, tablet: { width: 1024, height: 768, isMobile: false }, mobile: { width: 390, height: 844, isMobile: true } };
(async () => {
  const browser = await chromium.launch();
  const results = [];
  for (const [viewportName, viewport] of Object.entries(viewports)) {
    const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, isMobile: viewport.isMobile });
    const consoleMessages = [];
    const failedRequests = [];
    for (const route of routes) {
      const page = await context.newPage();
      page.on('console', msg => { if (['error','warning'].includes(msg.type())) consoleMessages.push({ route, type: msg.type(), text: msg.text() }); });
      page.on('requestfailed', req => failedRequests.push({ route, url: req.url(), method: req.method(), failure: req.failure()?.errorText || '' }));
      await page.goto(`${target}#${route}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(300);
      const base = `${route.toLowerCase().replace(/_/g, '-')}-${viewportName}`;
      const screenshot = path.join(outDir, `${base}.png`);
      await page.screenshot({ path: screenshot, fullPage: true });
      const info = await page.evaluate((screenshotPath) => {
        const bodyText = document.body.innerText;
        const controls = [...document.querySelectorAll('button, a, input, select, textarea')].map(el => ({
          tag: el.tagName.toLowerCase(),
          text: (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim(),
          aria: el.getAttribute('aria-label') || '',
          id: el.id || '',
          disabled: !!el.disabled,
          rect: (() => { const r = el.getBoundingClientRect(); return { width: Math.round(r.width), height: Math.round(r.height) }; })(),
        }));
        return {
          finalUrl: location.href,
          appVisible: !!document.querySelector('#app') && getComputedStyle(document.querySelector('#app')).display !== 'none',
          mainTitle: document.querySelector('.title')?.textContent?.trim() || '',
          overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          brokenImages: [...document.images].filter(img => !img.complete || img.naturalWidth === 0).map(img => img.currentSrc || img.src),
          focusables: [...document.querySelectorAll('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])')].length,
          unnamedControls: controls.filter(el => !el.text && !el.aria),
          tooSmallControls: controls.filter(el => (el.rect.width > 0 && el.rect.width < 44) || (el.rect.height > 0 && el.rect.height < 44)),
          forbiddenText: ['TypeError','ReferenceError','FirebaseError','Traceback','apiKey','secret','token'].filter(t => bodyText.includes(t)),
          screenshot: screenshotPath,
        };
      }, screenshot);
      results.push({ viewport: viewportName, route, ...info });
      await page.close();
    }
    results.push({ viewport: viewportName, route: 'RUNTIME_MESSAGES', consoleMessages, failedRequests });
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(outDir, 'fresh-route-diagnostics.json'), JSON.stringify({ target, createdAt: new Date().toISOString(), results }, null, 2));
})();
