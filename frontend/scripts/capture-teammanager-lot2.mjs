import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.LOT2_EVIDENCE_URL || 'http://127.0.0.1:5174/teammanager-lot2-audit.html';
const phase = process.env.LOT2_EVIDENCE_PHASE || 'before';
const outputDir = process.env.LOT2_EVIDENCE_DIR || `../artifacts/v1-07-lot2-teammanager-${phase}`;
const viewports = [
  { width: 1024, height: 900 },
  { width: 1440, height: 1000 },
];

const goldQuota = {
  plan: 'GOLD',
  dentistes_used: 1,
  dentistes_max: 1,
  secretaires_used: 0,
  secretaires_max: 2,
  pending_count: 0,
  can_add_dentiste: false,
  can_add_secretaire: true,
};

const rejected = {
  id: 77,
  email: 'refuse@example.test',
  role: 'SECRETAIRE',
  nom_complet: 'Collaborateur Refusé',
  telephone_mobile: null,
  is_active: false,
  approval_status: 'rejected',
  approval_note: null,
  created_at: '2026-09-19T09:00:00Z',
  permissions: { agenda: true, patients: true },
};

await fs.mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const evidence = [];

async function installRoutes(page, scenario) {
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    if (scenario === 'load-error' && pathname.startsWith('/api/team')) {
      return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Service indisponible' }) });
    }
    if (pathname === '/api/team/' || pathname === '/api/team') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(scenario === 'rejected' ? [rejected] : []),
      });
    }
    if (pathname === '/api/team/quota') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(goldQuota) });
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
}

async function capture(viewport, scenario) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const runtimeErrors = [];
  page.on('pageerror', error => runtimeErrors.push(`pageerror:${error.message}`));
  await installRoutes(page, scenario);
  await page.goto(baseUrl, { waitUntil: 'networkidle' });

  if (scenario === 'gold-partial') await page.getByText('GOLD', { exact: true }).waitFor();
  if (scenario === 'load-error') await page.waitForTimeout(150);
  if (scenario === 'rejected') {
    const row = page.getByText('Collaborateur Refusé').locator('xpath=ancestor::div[contains(@class,"group")]').first();
    await row.hover();
  }

  const screenshot = `${phase}-${scenario}-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, screenshot), fullPage: false });

  const snapshot = await page.evaluate(() => {
    const text = document.body.innerText;
    return {
      text,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
      hasGenericQuota: text.includes('Quota atteint — passez au plan supérieur'),
      hasSpecificGoldQuota: text.includes('Quota dentistes atteint — 2 place(s) assistante(s) disponible(s)'),
      hasFalseEmpty: text.includes("Aucun membre dans l'équipe"),
      hasLoadError: text.includes('Équipe non chargée'),
      hasReactivateButton: document.querySelector("[title=\"Réactiver l'accès\"]") !== null,
      hasSuspendButton: document.querySelector("[title=\"Suspendre l'accès\"]") !== null,
      hasRejectedBadge: text.includes('Refusé'),
    };
  });
  if (snapshot.horizontalOverflow) throw new Error(`${scenario} ${viewport.width}: horizontal overflow`);
  if (runtimeErrors.length) throw new Error(`${scenario} ${viewport.width}: ${runtimeErrors.join(' | ')}`);

  evidence.push({ scenario, viewport, screenshot, ...snapshot, runtimeErrors });
  await context.close();
}

try {
  for (const viewport of viewports) {
    for (const scenario of ['gold-partial', 'load-error', 'rejected']) {
      await capture(viewport, scenario);
    }
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence.map(item => ({ scenario: item.scenario, viewport: item.viewport, screenshot: item.screenshot })), null, 2));
