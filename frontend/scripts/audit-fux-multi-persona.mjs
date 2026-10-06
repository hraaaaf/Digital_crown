import { chromium, request } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const password = process.env.T2_PASSWORD;
const mainUser = process.env.T2_USER || 't2-browser@cabinet.ma';
if (!password) throw new Error('T2_PASSWORD required');

const BASE_URL = 'http://127.0.0.1:5173';
const API_URL = 'http://127.0.0.1:8005';
const OUT = path.resolve('..', 'audit-artifacts', 'fux-multi-persona');

await fs.rm(OUT, { recursive: true, force: true });
await fs.mkdir(OUT, { recursive: true });

const api = await request.newContext({ baseURL: API_URL });
const apiLogin = await api.post('/api/auth/login', {
  form: { username: mainUser, password },
});
if (!apiLogin.ok()) throw new Error(`API bootstrap login failed: ${apiLogin.status()} ${await apiLogin.text()}`);
const mainTokens = await apiLogin.json();
const patientResp = await api.get('/api/patients', {
  headers: { Authorization: `Bearer ${mainTokens.access_token}` },
});
if (!patientResp.ok()) throw new Error('Patient fixture read failed');
const patients = await patientResp.json();
const patient = patients.find((p) => p.numero_dossier === 'T2-0001') || patients[0];
if (!patient) throw new Error('No patient fixture available');
await api.dispose();

const browser = await chromium.launch({ headless: true });

const viewports = [
  { key: 'desktop', width: 1280, height: 900 },
  { key: 'mobile', width: 390, height: 844 },
];

const personas = [
  {
    key: 'dentiste-proprietaire',
    label: 'Dentiste propriétaire',
    email: mainUser,
    tasks: async (session) => {
      await session.go('/dashboard', '01-dashboard');
      await session.go('/patients', '02-patients');
      await session.go(`/patients/${patient.id}`, '03-patient-dossier');
      await session.go('/settings', '04-settings');
      await session.clickAndCapture(
        page => page.getByRole('button', { name: 'Sécurité & Backup', exact: true }),
        '05-security-backup',
      );
    },
  },
  {
    key: 'dentiste-collaborateur',
    label: 'Dentiste collaborateur pressé',
    email: mainUser,
    tasks: async (session) => {
      await session.go('/dashboard', '01-dashboard');
      await session.go(`/patients/${patient.id}?tab=analysis`, '02-analysis');
      await session.go(`/patients/${patient.id}?tab=admin`, '03-documents');
      await session.go('/agenda', '04-agenda');
    },
  },
  {
    key: 'assistante',
    label: 'Assistante',
    email: mainUser,
    implementationNote: 'No dedicated ASSISTANTE role exists in UserRole; this is a workflow-perspective audit on the authenticated cabinet surface.',
    tasks: async (session) => {
      await session.go('/agenda', '01-agenda');
      await session.go('/patients', '02-patients');
      await session.go(`/patients/${patient.id}`, '03-patient-dossier');
      await session.go(`/patients/${patient.id}?tab=admin`, '04-documents');
    },
  },
  {
    key: 'secretaire',
    label: 'Secrétaire',
    email: 't2-restricted@cabinet.ma',
    tasks: async (session) => {
      await session.go('/dashboard', '01-dashboard');
      await session.go('/agenda', '02-agenda');
      await session.go('/patients', '03-patients-denied', { expectedRedirect: '/dashboard' });
      await session.go('/accounting', '04-accounting-denied', { expectedRedirect: '/dashboard' });
      await session.go('/settings', '05-settings-denied', { expectedRedirect: '/dashboard' });
    },
  },
  {
    key: 'technicien',
    label: 'Technicien',
    email: mainUser,
    implementationNote: 'No dedicated TECHNICIEN role exists in UserRole; this is a technical-support workflow-perspective audit.',
    tasks: async (session) => {
      await session.go('/hub?select=1', '01-hub');
      await session.go('/control-center', '02-control-center');
      await session.go('/settings', '03-settings');
      await session.clickAndCapture(
        page => page.getByRole('button', { name: 'Sécurité & Backup', exact: true }),
        '04-security-backup',
      );
      await session.clickAndCapture(
        page => page.getByRole('button', { name: 'Performance & Assistance', exact: true }),
        '05-performance-assistance',
      );
    },
  },
];

const report = {
  evaluatedSha: process.env.GITHUB_SHA || null,
  generatedAt: new Date().toISOString(),
  product: 'Digital Crown',
  audit: 'First User Experience multi-persona',
  personas: [],
};

function safeName(value) {
  return String(value).replace(/[^a-z0-9_-]+/gi, '-').replace(/^-+|-+$/g, '').toLowerCase();
}

async function collectMetrics(page) {
  return page.evaluate(() => {
    const visible = (el) => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
    };
    const els = [...document.querySelectorAll('a,button,input,select,textarea,[role="button"],[role="link"]')].filter(visible);
    const interactive = els.map((el) => {
      const rect = el.getBoundingClientRect();
      const text = (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || el.getAttribute('placeholder') || '').trim();
      return {
        tag: el.tagName.toLowerCase(),
        text: text.slice(0, 120),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
      };
    });
    const unlabeled = interactive.filter((x) => !x.text);
    const tiny = interactive.filter((x) => x.width < 44 || x.height < 44);
    const headings = [...document.querySelectorAll('h1,h2,h3,[role="heading"]')]
      .filter(visible)
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean)
      .slice(0, 30);
    const main = document.querySelector('main');
    const mainText = ((main?.textContent || document.body.textContent || '')).replace(/\s+/g, ' ').trim();
    return {
      title: document.title,
      path: location.pathname + location.search,
      headings,
      interactiveCount: interactive.length,
      visibleInteractiveSample: interactive.slice(0, 80),
      unlabeledInteractiveCount: unlabeled.length,
      smallTargetCountUnder44: tiny.length,
      smallTargetSample: tiny.slice(0, 25),
      horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
      bodyTextLength: (document.body.textContent || '').length,
      mainTextExcerpt: mainText.slice(0, 1800),
    };
  });
}

async function createSession(persona, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    colorScheme: 'light',
  });
  // run-with-t2-workstation injects owner auth + workstation cookies. Preserve only
  // the workstation identity so each persona starts from a genuinely signed-out web session.
  await context.clearCookies({ name: 'access_token' });
  await context.clearCookies({ name: 'refresh_token' });
  await context.addInitScript(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('token');
  });
  const page = await context.newPage();
  const events = [];
  const consoleErrors = [];
  const pageErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => pageErrors.push(err.message));

  async function capture(step, extra = {}) {
    await page.waitForTimeout(650);
    const metrics = await collectMetrics(page);
    const file = `${safeName(persona.key)}-${viewport.key}-${safeName(step)}.jpg`;
    await page.screenshot({
      path: path.join(OUT, file),
      type: 'jpeg',
      quality: 72,
      fullPage: false,
      animations: 'disabled',
    });
    const item = {
      step,
      screenshot: file,
      url: page.url(),
      metrics,
      consoleErrors: [...consoleErrors],
      pageErrors: [...pageErrors],
      ...extra,
    };
    events.push(item);
    consoleErrors.length = 0;
    pageErrors.length = 0;
    return item;
  }

  async function go(route, step, options = {}) {
    const started = Date.now();
    let status = 'OK';
    let error = null;
    try {
      await page.goto(`${BASE_URL}${route}`, { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.waitForTimeout(900);
    } catch (err) {
      status = 'BLOCKED';
      error = err instanceof Error ? err.message : String(err);
    }
    const actualPath = new URL(page.url()).pathname;
    const redirectMatched = options.expectedRedirect ? actualPath === options.expectedRedirect : null;
    return capture(step, {
      status,
      error,
      navigationMs: Date.now() - started,
      expectedRedirect: options.expectedRedirect || null,
      redirectMatched,
    });
  }

  async function clickAndCapture(locatorFactory, step) {
    const started = Date.now();
    let status = 'OK';
    let error = null;
    try {
      const locator = locatorFactory(page);
      await locator.waitFor({ state: 'visible', timeout: 8000 });
      await locator.click();
      await page.waitForTimeout(700);
    } catch (err) {
      status = 'BLOCKED';
      error = err instanceof Error ? err.message : String(err);
    }
    return capture(step, {
      status,
      error,
      interactionMs: Date.now() - started,
    });
  }

  async function login() {
    const started = Date.now();
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForTimeout(650);
    await capture('00-login');
    let status = 'OK';
    let error = null;
    try {
      await page.getByPlaceholder('nom@cabinet.com').fill(persona.email);
      await page.getByPlaceholder('••••••••').fill(password);
      await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
      await page.waitForFunction(() => location.pathname !== '/login', null, { timeout: 30000 });
      await page.waitForTimeout(1200);
    } catch (err) {
      status = 'BLOCKED';
      error = err instanceof Error ? err.message : String(err);
    }
    return capture('00-authenticated-entry', {
      status,
      error,
      loginToEntryMs: Date.now() - started,
    });
  }

  return { context, page, events, go, clickAndCapture, login };
}

for (const viewport of viewports) {
  for (const persona of personas) {
    const session = await createSession(persona, viewport);
    const personaReport = {
      key: persona.key,
      label: persona.label,
      viewport: `${viewport.width}x${viewport.height}`,
      identity: persona.email,
      implementationNote: persona.implementationNote || null,
      steps: session.events,
    };
    try {
      await session.login();
      await persona.tasks(session);
    } catch (err) {
      personaReport.fatal = err instanceof Error ? err.message : String(err);
      try {
        await session.page.screenshot({
          path: path.join(OUT, `${safeName(persona.key)}-${viewport.key}-fatal.jpg`),
          type: 'jpeg',
          quality: 72,
          fullPage: false,
          animations: 'disabled',
        });
      } catch {}
    } finally {
      personaReport.steps = session.events;
      report.personas.push(personaReport);
      await session.context.close();
    }
  }
}

await browser.close();

const summary = {
  evaluatedSha: report.evaluatedSha,
  personaRuns: report.personas.length,
  blockedSteps: report.personas.flatMap((p) => p.steps.map((s) => ({ persona: p.label, viewport: p.viewport, ...s }))).filter((s) => s.status === 'BLOCKED').length,
  redirectMismatches: report.personas.flatMap((p) => p.steps.map((s) => ({ persona: p.label, viewport: p.viewport, ...s }))).filter((s) => s.expectedRedirect && s.redirectMatched === false).length,
  overflowScreens: report.personas.flatMap((p) => p.steps.map((s) => ({ persona: p.label, viewport: p.viewport, ...s }))).filter((s) => s.metrics?.horizontalOverflow).length,
  screensWithUnlabeledInteractive: report.personas.flatMap((p) => p.steps.map((s) => ({ persona: p.label, viewport: p.viewport, ...s }))).filter((s) => (s.metrics?.unlabeledInteractiveCount || 0) > 0).length,
  screensWithSmallTargets: report.personas.flatMap((p) => p.steps.map((s) => ({ persona: p.label, viewport: p.viewport, ...s }))).filter((s) => (s.metrics?.smallTargetCountUnder44 || 0) > 0).length,
};

await fs.writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
await fs.writeFile(path.join(OUT, 'summary.json'), JSON.stringify(summary, null, 2));
await fs.writeFile(
  path.join(OUT, 'README.md'),
  [
    '# Digital Crown — FUX multi-persona evidence',
    '',
    `Evaluated SHA: ${report.evaluatedSha || 'unknown'}`,
    `Generated: ${report.generatedAt}`,
    '',
    'Personas: Dentiste propriétaire, Dentiste collaborateur pressé, Assistante, Secrétaire, Technicien.',
    'Viewports: 1280x900 and 390x844.',
    '',
    'Important role-model limitation: current UserRole exposes ADMIN, DENTISTE, SECRETAIRE only. Assistante and Technicien are audited as workflow perspectives, not distinct authorization roles.',
    '',
    'See report.json for per-step timings, visible headings/interactions, redirects, console/page errors, horizontal overflow and target-size heuristics.',
  ].join('\n'),
);

console.log('FUX_MULTI_PERSONA_SUMMARY=' + JSON.stringify(summary));
