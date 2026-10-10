import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const phase = process.env.V15_03_1_PHASE || 'before';
const out = path.resolve(`artifacts/v15-03-1-kiosk-shell-${phase}`);
await fs.mkdir(out, { recursive: true });

const bootstrap = {
  workstationId: 'ws-kiosk-proof',
  defaultExperience: 'station',
  stationLocked: true,
  stationEscapeAuthorized: false,
  stationEscapeExpiresAt: null,
  enrollmentRequired: false,
  authenticated: true,
  pinConfigured: true,
  canManage: false,
  canConfigurePin: false,
};

const viewports = [
  { width: 390, height: 844, label: '390x844' },
  { width: 430, height: 932, label: '430x932' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
];
const scales = [
  { label: 'normal', rootFontSize: null },
  { label: 'text200', rootFontSize: '200%' },
];
const languages = [
  { code: 'fr', button: 'Français', heading: 'Bienvenue au cabinet', dir: 'ltr' },
  { code: 'ar', button: 'العربية', heading: 'مرحباً بكم في العيادة', dir: 'rtl' },
  { code: 'en', button: 'English', heading: 'Welcome to the clinic', dir: 'ltr' },
];

const browser = await chromium.launch({ headless: true });
const report = [];

try {
  for (const vp of viewports) {
    for (const scale of scales) {
      const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
      await context.route('**/api/workstation/bootstrap', route => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(bootstrap),
      }));
      await context.route('**/api/workstation/state', route => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(bootstrap),
      }));

      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {
        if (message.type() === 'error') errors.push(message.text());
      });

      await page.goto('http://127.0.0.1:4195/station', {
        waitUntil: 'networkidle',
        timeout: 30000,
      });
      if (scale.rootFontSize) {
        await page.evaluate(value => { document.documentElement.style.fontSize = value; }, scale.rootFontSize);
        await page.waitForTimeout(100);
      }

      for (const language of languages) {
        // Exercise the actual public language buttons. Never inject dir/lang.
        await page.getByRole('button', { name: language.button, exact: true }).click();
        const meta = await page.evaluate(() => {
          const shell = document.querySelector('[data-workstation-experience="station"]');
          const touchTargets = [...document.querySelectorAll(
            '[data-station-action], button[aria-pressed], button[aria-label="Digital Crown"]',
          )];
          return {
            width: document.documentElement.clientWidth,
            scrollWidth: document.documentElement.scrollWidth,
            height: document.documentElement.clientHeight,
            scrollHeight: document.documentElement.scrollHeight,
            stationVisible: Boolean(shell),
            screen: shell?.getAttribute('data-station-screen') || null,
            language: shell?.getAttribute('data-station-language') || null,
            lang: shell?.getAttribute('lang') || null,
            dir: shell?.getAttribute('dir') || null,
            selectedLanguages: [...document.querySelectorAll('button[aria-pressed="true"]')]
              .map(node => node.getAttribute('aria-label')),
            tooSmallTargets: touchTargets.flatMap(node => {
              const rect = node.getBoundingClientRect();
              return rect.width < 44 || rect.height < 44
                ? [{ label: node.getAttribute('aria-label') || node.textContent?.trim(), width: rect.width, height: rect.height }]
                : [];
            }),
            cardTextOverflow: [...document.querySelectorAll('[data-station-action]')].flatMap(card => {
              const cardBox = card.getBoundingClientRect();
              return [...card.querySelectorAll('span.block')].flatMap(node => {
                const range = document.createRange();
                range.selectNodeContents(node);
                const protrudes = [...range.getClientRects()].some(line =>
                  line.left < cardBox.left - 1 || line.right > cardBox.right + 1
                );
                return protrudes || node.scrollWidth > node.clientWidth + 1
                  ? [{ action: card.getAttribute('data-station-action'), text: node.textContent?.trim(), protrudes }]
                  : [];
              });
            }),
            clinicalLinks: [...document.querySelectorAll('a')]
              .filter(a => /patients|agenda|accounting|dashboard|settings/i.test(a.getAttribute('href') || ''))
              .map(a => a.getAttribute('href')),
            h1: document.querySelector('h1')?.textContent || '',
          };
        });

        const filename = `${phase}-station-${vp.label}-${scale.label}-${language.code}.png`;
        await page.screenshot({
          path: path.join(out, filename),
          fullPage: true,
          animations: 'disabled',
        });
        report.push({
          phase,
          viewport: vp.label,
          scale: scale.label,
          expectedLanguage: language.code,
          expectedDir: language.dir,
          expectedHeading: language.heading,
          expectedButton: language.button,
          filename,
          ...meta,
          errors: [...errors],
        });
      }
      await context.close();
    }
  }
} finally {
  await browser.close();
}

const evidence = {
  phase,
  head: process.env.EVALUATED_SHA || process.env.GITHUB_SHA || null,
  base: process.env.EVALUATED_BASE || null,
  report,
};
await fs.writeFile(path.join(out, 'evidence.json'), JSON.stringify(evidence, null, 2));

const failures = report.filter(item =>
  !item.stationVisible ||
  item.screen !== 'home' ||
  item.language !== item.expectedLanguage ||
  item.lang !== item.expectedLanguage ||
  item.dir !== item.expectedDir ||
  item.h1 !== item.expectedHeading ||
  item.selectedLanguages.length !== 1 ||
  item.selectedLanguages[0] !== item.expectedButton ||
  item.tooSmallTargets.length > 0 ||
  item.cardTextOverflow.length > 0 ||
  item.scrollWidth > item.width ||
  item.clinicalLinks.length > 0 ||
  item.errors.length > 0
);
console.log(JSON.stringify(evidence, null, 2));
if (failures.length > 0) {
  console.error('V1.5-03.1 visual evidence failed closed:', JSON.stringify(failures, null, 2));
  process.exit(1);
}
