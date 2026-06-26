import { Page, Route } from '@playwright/test';

export const API = 'http://localhost:8005/api';

// ── Fake JWT (valide jusqu'en 2099, passe isTokenExpired) ────────────────────
// Standard base64 (NOT base64url) so browser atob() can decode it.
// btoa('{"alg":"HS256","typ":"JWT"}')  → no padding needed (27 bytes → 36 chars)
// btoa('{"sub":"1","exp":4091289600}') → needs == padding  (28 bytes → 38+2 chars)
const _h = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9';
const _p = 'eyJzdWIiOiIxIiwiZXhwIjo0MDkxMjg5NjAwfQ==';
export const FAKE_TOKEN = `${_h}.${_p}.fake_e2e_signature`;

// ── Fake data ─────────────────────────────────────────────────────────────────

export const FAKE_USER = {
  id: 1,
  email: 'dentiste@test.com',
  nom_complet: 'Dr. Ahmed Test',
  role: 'ADMIN',
  is_active: true,
  employer_id: 1,
  subscription_plan: 'PREMIUM',
  permissions: ['patients', 'agenda', 'accounting', 'cephalo'],
};

export const FAKE_PATIENT = {
  id: 42,
  nom: 'BENALI',
  prenom: 'Youssef',
  numero_dossier: 'P-000042',
  date_naissance: '1990-05-15',
  telephone: '0661234567',
  email: 'youssef.benali@email.com',
  antecedents_medicaux: '',
  employer_id: 1,
};

export const FAKE_CABINET = {
  id: 1,
  nom_cabinet: 'Cabinet Dentaire Test',
  nom_praticien: 'Dr. Ahmed Test',
  adresse: '10 Rue des Tests, Casablanca',
  telephone: '0522000000',
  selected_template: 'swiss',
};

// ── Mock helpers ──────────────────────────────────────────────────────────────

/** Injecte token + user dans localStorage avant le chargement de la page. */
export async function injectAuth(page: Page) {
  await page.addInitScript(({ token, user }: { token: string; user: typeof FAKE_USER }) => {
    localStorage.setItem('token', token);
    localStorage.setItem('dc_user', JSON.stringify(user));
    // Persist Zustand auth store so ProtectedRoute doesn't redirect
    localStorage.setItem('auth-storage', JSON.stringify({
      state: { user, isAuthenticated: true },
      version: 0,
    }));
  }, { token: FAKE_TOKEN, user: FAKE_USER });
}

/**
 * Mocke tous les appels API backend (port 8005) via un handler unique.
 * Pattern '**' pour intercepter peu importe si Chrome résout localhost → 127.0.0.1.
 * Le handler filtre par port :8005 et laisse passer le reste (frontend 5173).
 */
export async function mockAllApi(page: Page) {
  await page.route('**', (route: Route) => {
    const url = route.request().url();
    const method = route.request().method().toUpperCase();

    // Only intercept backend requests (port 8005) — let frontend through
    if (!url.includes(':8005')) {
      return route.continue();
    }

    // ── Santé backend ────────────────────────────────────────────────────────
    if (url.endsWith('/health') || url.includes('/health?')) {
      return route.fulfill({ json: { status: 'ok' } });
    }

    // ── Auth ─────────────────────────────────────────────────────────────────
    if (url.includes('/auth/login')) {
      return route.fulfill({ json: { access_token: FAKE_TOKEN, token_type: 'bearer' } });
    }
    if (url.includes('/auth/me')) {
      return route.fulfill({ json: FAKE_USER });
    }
    if (url.includes('/auth/refresh')) {
      return route.fulfill({ json: { access_token: FAKE_TOKEN } });
    }
    if (url.includes('/auth/logout')) {
      return route.fulfill({ status: 200, json: { ok: true } });
    }

    // ── Cabinet / clinique ───────────────────────────────────────────────────
    if (url.includes('/clinics/init-status')) {
      return route.fulfill({ json: { is_initialized: true } });
    }
    if (url.includes('/clinics/recheck-license')) {
      return route.fulfill({ json: { ok: true } });
    }
    if (url.includes('/cabinet/config')) {
      return route.fulfill({ json: FAKE_CABINET });
    }
    if (url.includes('/clinics/me') || url.match(/\/clinics\/\d+/)) {
      return route.fulfill({ json: FAKE_CABINET });
    }
    if (url.includes('/clinics')) {
      return route.fulfill({ json: FAKE_CABINET });
    }

    // ── Patients ─────────────────────────────────────────────────────────────
    if (url.includes('/patients/fantomes')) {
      return route.fulfill({ json: [] });
    }
    if (url.includes('/patients/next-dossier-number')) {
      return route.fulfill({ json: { numero: 'P-000043' } });
    }
    if (url.includes('/patients/check-dossier/')) {
      return route.fulfill({ json: { available: true } });
    }
    if (url.includes('/patients/check-duplicate')) {
      return route.fulfill({ json: { is_duplicate: false } });
    }
    if (url.includes('/ai-summary')) {
      return route.fulfill({ json: { last_visit: null, clinical_summary: 'RAS', alerts: [], risk_level: 'low' } });
    }
    if (url.match(/\/patients\/\d+\//)) {
      return route.fulfill({ json: [] });
    }
    if (url.match(/\/patients\/\d+$/)) {
      return route.fulfill({ json: FAKE_PATIENT });
    }
    if (url.includes('/patients')) {
      if (method === 'POST') return route.fulfill({ status: 201, json: { ...FAKE_PATIENT, id: 99 } });
      return route.fulfill({ json: [FAKE_PATIENT] });
    }

    // ── Actes / agenda ───────────────────────────────────────────────────────
    if (url.includes('/actes')) {
      return route.fulfill({ json: [] });
    }
    if (url.includes('/appointments')) {
      return route.fulfill({ json: [] });
    }

    // ── Notifications / équipe ───────────────────────────────────────────────
    if (url.includes('/notifications')) {
      return route.fulfill({ json: [] });
    }
    if (url.includes('/team/quota')) {
      return route.fulfill({ json: { plan: 'PREMIUM', can_add_dentist: true, can_add_assistant: true } });
    }

    // ── Cephalo ──────────────────────────────────────────────────────────────
    if (url.includes('/cephalo')) {
      return route.fulfill({ json: [] });
    }

    // ── Comptabilité / analytics ─────────────────────────────────────────────
    if (url.includes('/accounting')) {
      return route.fulfill({ json: [] });
    }
    if (url.includes('/analytics')) {
      return route.fulfill({ json: {} });
    }

    // ── Documents / archives ─────────────────────────────────────────────────
    if (url.includes('/documents')) {
      return route.fulfill({ json: [] });
    }
    if (url.includes('/archives')) {
      return route.fulfill({ json: [] });
    }

    // ── Divers ───────────────────────────────────────────────────────────────
    if (url.includes('/bot')) return route.fulfill({ json: {} });
    if (url.includes('/templates')) return route.fulfill({ json: [] });
    if (url.includes('/ia')) return route.fulfill({ json: {} });

    // Catch-all — fulfills any unknown backend request silently
    return route.fulfill({ json: {} });
  });
}
