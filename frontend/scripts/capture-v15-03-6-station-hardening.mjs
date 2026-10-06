import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const phase = process.env.V15_03_6_PHASE || 'after';
const out = path.resolve(`artifacts/v15-03-6-station-hardening-${phase}`);
await fs.mkdir(out, { recursive: true });

const bootstrap = {
  workstationId: 'ws-03-6-proof',
  displayName: 'Accueil 1',
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
const contrastThemes = ['default', 'emerald', 'rose', 'prestige', 'ocean', 'graphite', 'dark', 'high-contrast'];

const parseRgb = (value) => {
  const match = value.match(/rgba?\((\d+)\D+(\d+)\D+(\d+)/i);
  if (!match) throw new Error(`Unsupported computed color: ${value}`);
  return [Number(match[1]), Number(match[2]), Number(match[3])];
};
const relativeLuminance = (value) => {
  const channels = parseRgb(value).map(component => {
    const c = component / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
};
const contrastRatio = (foreground, background) => {
  const a = relativeLuminance(foreground);
  const b = relativeLuminance(background);
  const lighter = Math.max(a, b);
  const darker = Math.min(a, b);
  return (lighter + 0.05) / (darker + 0.05);
};

const onePixelPng = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
const browser = await chromium.launch({ headless: true });
const report = [];

try {
  for (const vp of viewports) {
    for (const scale of scales) {
      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        reducedMotion: 'reduce',
      });

      await context.route('**/api/workstation/bootstrap*', route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(bootstrap),
      }));
      await context.route('**/api/workstation/state*', route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(bootstrap),
      }));
      await context.route('**/api/workstation/patient-session/config*', route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify({ fallbackMode: 'disabled' }),
      }));
      await context.route('**/api/workstation/patient-session', route => {
        if (route.request().method() !== 'POST') return route.continue();
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            sessionId: 'proof-session-036',
            handoffUrl: 'https://cabinet.local/companion?stationSession=opaque-proof-token',
            qrDataUrl: onePixelPng,
            nfcPayload: 'https://cabinet.local/companion?stationSession=opaque-proof-token',
            expiresAt: new Date(Date.now() + 120_000).toISOString(),
            fallbackMode: 'disabled',
          }),
        });
      });
      await context.route('**/api/workstation/patient-session/proof-session-036', route => {
        if (route.request().method() !== 'GET') return route.continue();
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'identified',
            sessionId: 'proof-session-036',
            displayName: 'Aya Audit',
            claimedAt: new Date().toISOString(),
          }),
        });
      });
      await context.route('**/api/workstation/patient-session/proof-session-036/appointments/today', route => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'single',
          staffActionRequired: false,
          appointments: [{
            appointmentId: 36,
            datetimeStart: '2026-10-05T16:30:00',
            durationMinutes: 30,
            schedulingType: 'EXACT_TIME',
            status: 'CONFIRMÉ',
          }],
        }),
      }));
      await context.route('**/api/workstation/patient-session/proof-session-036/appointments/36/arrive', route => route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'offline-proof' }),
      }));
      await context.route('**/api/workstation/patient-session/proof-session-036/purge', route => route.fulfill({ status: 204, body: '' }));

      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {
        if (message.type() !== 'error') return;
        const value = message.text();
        if (/503|offline-proof|proof-session-036\/appointments\/36\/arrive/i.test(value)) return;
        errors.push(value);
      });

      await page.goto('http://127.0.0.1:4198/station', { waitUntil: 'networkidle', timeout: 30000 });
      await page.addStyleTag({
        content: '*,*::before,*::after{transition:none !important;animation:none !important;}',
      });
      if (scale.rootFontSize) {
        await page.evaluate(value => { document.documentElement.style.fontSize = value; }, scale.rootFontSize);
        await page.waitForTimeout(100);
      }

      await page.locator('[data-workstation-experience="station"]').waitFor();
      const reducedMotion = await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
      const originalTheme = await page.evaluate(() => ({
        html: document.documentElement.getAttribute('data-theme'),
        body: document.body.getAttribute('data-theme'),
      }));
      const themeContrasts = [];
      const primaryProbe = page.getByRole('button', { name: 'Français', exact: true });
      for (const theme of contrastThemes) {
        await page.evaluate(themeName => {
          for (const node of [document.documentElement, document.body]) {
            if (themeName === 'default') node.removeAttribute('data-theme');
            else node.setAttribute('data-theme', themeName);
          }
        }, theme);
        const colors = await primaryProbe.evaluate(node => {
          const style = getComputedStyle(node);
          return { foreground: style.color, background: style.backgroundColor };
        });
        themeContrasts.push({
          theme,
          ...colors,
          ratio: Number(contrastRatio(colors.foreground, colors.background).toFixed(2)),
        });
      }
      await page.evaluate(saved => {
        const restore = (node, value) => {
          if (value === null) node.removeAttribute('data-theme');
          else node.setAttribute('data-theme', value);
        };
        restore(document.documentElement, saved.html);
        restore(document.body, saved.body);
      }, originalTheme);

      const homeMeta = await page.evaluate(() => ({
        width: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        clinicalLinks: Array.from(document.querySelectorAll('a'))
          .filter(a => /patients|agenda|accounting|dashboard|settings/i.test(a.getAttribute('href') || ''))
          .map(a => a.getAttribute('href')),
      }));
      await page.screenshot({
        path: path.join(out, `${phase}-home-${vp.label}-${scale.label}.png`),
        fullPage: true,
        animations: 'disabled',
      });

      await page.locator('[data-station-action="appointment"]').click();
      await page.locator('[data-station-arrival-bridge]').waitFor({ timeout: 10000 });
      await page.getByRole('button', { name: 'Confirmer mon arrivée' }).click();
      await page.getByRole('alert').filter({ hasText: 'Arrivée non confirmée' }).waitFor({ timeout: 10000 });

      const offlineMeta = await page.evaluate(() => ({
        width: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        bodyText: document.body.textContent || '',
        arrivedVisible: Boolean(document.querySelector('[data-station-arrival-confirmed]')),
        patientNameVisible: (document.body.textContent || '').includes('Aya Audit'),
        technicalToastVisible: Array.from(document.querySelectorAll('[role="status"]'))
          .some(node => /Erreur Serveur|Serveur injoignable|Mode hors-ligne/i.test(node.textContent || '')),
      }));
      await page.screenshot({
        path: path.join(out, `${phase}-offline-arrival-${vp.label}-${scale.label}.png`),
        fullPage: true,
        animations: 'disabled',
      });

      report.push({
        phase,
        viewport: vp.label,
        scale: scale.label,
        reducedMotion,
        homeOverflow: homeMeta.scrollWidth > homeMeta.width,
        offlineOverflow: offlineMeta.scrollWidth > offlineMeta.width,
        clinicalLinks: homeMeta.clinicalLinks,
        arrivedVisible: offlineMeta.arrivedVisible,
        patientNameVisible: offlineMeta.patientNameVisible,
        technicalToastVisible: offlineMeta.technicalToastVisible,
        offlineErrorVisible: /Arrivée non confirmée/.test(offlineMeta.bodyText),
        themeContrasts,
        errors,
      });

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
  !item.reducedMotion ||
  item.homeOverflow ||
  item.offlineOverflow ||
  item.clinicalLinks.length > 0 ||
  item.arrivedVisible ||
  !item.patientNameVisible ||
  (phase === 'before' ? !item.technicalToastVisible : item.technicalToastVisible) ||
  !item.offlineErrorVisible ||
  (phase === 'after' && item.themeContrasts.some(entry => entry.ratio < 4.5)) ||
  item.errors.length > 0
);
console.log(JSON.stringify(evidence, null, 2));
if (failures.length) {
  console.error('V1.5-03.6 station hardening evidence failed closed:', JSON.stringify(failures, null, 2));
  process.exit(1);
}
