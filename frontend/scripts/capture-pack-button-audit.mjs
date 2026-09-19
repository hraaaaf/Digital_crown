import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PACK_EVIDENCE_URL || 'http://127.0.0.1:5174/pack-button-audit.html';
const phase = process.env.PACK_EVIDENCE_PHASE || 'before';
const outputDir = process.env.PACK_EVIDENCE_DIR || `../artifacts/v1-07-pack-buttons-${phase}`;
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

const client = {
  id: 42,
  nom_complet: 'Dr Audit Pack',
  email: 'audit-pack@example.test',
  telephone: '',
  cabinet_name: 'Cabinet Audit Pack',
  is_licensed: true,
  license_expires_at: '2030-01-01T00:00:00Z',
  created_at: '2026-01-01T00:00:00Z',
  is_archived: false,
  is_suspended: false,
  internal_notes: null,
  last_login_at: null,
  subscription_plan: 'ELITE',
  stats: { total_patients: 12, total_ia_panoramique: 0, total_ia_cephalo: 0 },
};

await fs.mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const evidence = [];

async function installRoutes(page, scenario) {
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    const method = route.request().method();

    if (scenario === 'team-load-error' && pathname.startsWith('/api/team')) {
      return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Service indisponible' }) });
    }
    if (pathname === '/api/team/' || pathname === '/api/team') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(scenario === 'team-rejected' ? [rejected] : []),
      });
    }
    if (pathname === '/api/team/quota') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(goldQuota) });
    }

    if (pathname === '/api/superadmin/clients' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([client]) });
    }
    if (pathname === '/api/superadmin/trial-codes' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
    }
    if (pathname === '/api/superadmin/clients/42/plan' && method === 'PATCH') {
      return route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Passage au pack GOLD impossible : équipe réservée 2 dentiste(s) / 3 assistante(s), limites cibles 1 / 2.' }),
      });
    }
    if (pathname === '/api/superadmin/clients/42/send-renewal-email' && method === 'POST') {
      return route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ detail: "Aucun numéro de téléphone trouvé pour l'envoi WhatsApp." }),
      });
    }
    if (pathname.includes('/license-history')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
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
  const view = scenario.startsWith('superadmin') ? 'superadmin' : 'team';
  await page.goto(`${baseUrl}?view=${view}`, { waitUntil: 'networkidle' });

  if (scenario === 'team-gold-partial') {
    await page.getByText('GOLD', { exact: true }).waitFor();
  }
  if (scenario === 'team-load-error') {
    await page.waitForTimeout(150);
  }
  if (scenario === 'team-rejected') {
    const row = page.getByText('Collaborateur Refusé').locator('xpath=ancestor::div[contains(@class,"group")]').first();
    await row.hover();
  }
  if (scenario === 'superadmin-downgrade') {
    await page.getByText('Dr Audit Pack', { exact: true }).waitFor();
    await page.getByDisplayValue('ELITE').selectOption('GOLD');
    await page.waitForTimeout(150);
  }
  if (scenario === 'superadmin-renewal') {
    await page.getByText('Dr Audit Pack', { exact: true }).waitFor();
    await page.getByTitle('Email de relance').click();
    await page.waitForTimeout(150);
  }

  const screenshot = `${phase}-${scenario}-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, screenshot), fullPage: false });

  const snapshot = await page.evaluate(() => ({
    text: document.body.innerText,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
  }));
  if (snapshot.horizontalOverflow) throw new Error(`${scenario} ${viewport.width}: horizontal overflow`);
  if (runtimeErrors.length) throw new Error(`${scenario} ${viewport.width}: ${runtimeErrors.join(' | ')}`);

  evidence.push({ scenario, viewport, screenshot, ...snapshot, runtimeErrors });
  await context.close();
}

try {
  for (const viewport of viewports) {
    for (const scenario of [
      'team-gold-partial',
      'team-load-error',
      'team-rejected',
      'superadmin-downgrade',
      'superadmin-renewal',
    ]) {
      await capture(viewport, scenario);
    }
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence.map(item => ({ scenario: item.scenario, viewport: item.viewport, screenshot: item.screenshot })), null, 2));
