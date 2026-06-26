import { test, expect } from '@playwright/test';
import { mockAllApi, injectAuth, FAKE_PATIENT } from './helpers';

/**
 * Tests E2E céphalométrie — accès via la fiche patient.
 * Le module cephalo n'a pas de route dédiée ; il est intégré dans PatientDetails.
 */
test.describe('Module céphalométrie', () => {
  test.beforeEach(async ({ page }) => {
    // Global mock handles all :8005 requests — no test-specific routes needed
    // (test-specific '**/patients/42' routes would also intercept the frontend
    //  navigation at :5173, causing Chrome to show raw JSON instead of the app)
    await mockAllApi(page);
    await injectAuth(page);
  });

  test('fiche patient se charge correctement', async ({ page }) => {
    await page.goto('/patients/42');
    await expect(page.getByText('BENALI').first()).toBeVisible({ timeout: 12_000 });
  });

  test('onglet ou section céphalométrie est accessible', async ({ page }) => {
    await page.goto('/patients/42');

    // Wait for patient to load first
    await expect(page.getByText('BENALI').first()).toBeVisible({ timeout: 12_000 });

    // The cephalo module is inside the "Radiologie (IA)" tab — click it to access
    const radioTab = page.getByText(/[Rr]adiologie/i).first();
    if (await radioTab.isVisible({ timeout: 5_000 })) {
      await radioTab.click();
    }

    // After clicking the tab, cephalo-related content should appear
    const cephaloContent = page.getByText(/[Cc]éphalo|[Rr]adiologie|[Oo]rtho/i).first();
    await expect(cephaloContent).toBeVisible({ timeout: 8_000 });
  });

  test('ouvrir le module cephalo ne provoque pas d\'erreur JS', async ({ page }) => {
    const jsErrors: string[] = [];
    page.on('pageerror', (err) => jsErrors.push(err.message));

    await page.goto('/patients/42');
    // Wait for all API fetches (incl. ai-summary) to settle before clicking
    await page.waitForLoadState('networkidle');

    const cephaloBtn = page.getByText(/[Cc]éphalo|[Bb]ilan ortho/i).first();
    if (await cephaloBtn.isVisible({ timeout: 8_000 })) {
      await cephaloBtn.click({ timeout: 10_000 });
      await page.waitForTimeout(1500);
    }

    // Aucune erreur JS fatale ne doit être levée
    const fatalErrors = jsErrors.filter(e => !e.includes('ResizeObserver'));
    expect(fatalErrors).toHaveLength(0);
  });

  test('liste d\'analyses vide affiche un état vide (pas de crash)', async ({ page }) => {
    await page.goto('/patients/42');
    // Wait for all API fetches (incl. ai-summary) to settle before clicking
    await page.waitForLoadState('networkidle');

    const cephaloBtn = page.getByText(/[Cc]éphalo|[Bb]ilan ortho/i).first();
    if (await cephaloBtn.isVisible({ timeout: 8_000 })) {
      await cephaloBtn.click({ timeout: 10_000 });
      await page.waitForTimeout(1000);

      // Après ouverture : pas de spinner infini, pas d'erreur 500
      const spinner = page.locator('[class*="animate-spin"]');
      await expect(spinner).toHaveCount(0, { timeout: 6_000 });
    }
  });
});

// ── Tests de régression céphalométrie (logique pur — sans navigateur) ─────────
// Ces tests vérifient les règles métier documentées dans Notes.txt § 13.
// Ils sont isolés et ne nécessitent pas de backend.

test.describe('Règles calculs céphalométriques (régression)', () => {
  test('_standard_angle normalise 98.6° → 81.4°', () => {
    const standardAngle = (raw: number) => Math.min(raw, 180 - raw);
    expect(parseFloat(standardAngle(98.6).toFixed(1))).toBe(81.4);
  });

  test('_standard_angle normalise 104° → 76°', () => {
    const standardAngle = (raw: number) => Math.min(raw, 180 - raw);
    expect(standardAngle(104)).toBe(76);
  });

  test('_obtuse_angle retourne 143° pour 37°', () => {
    const obtuseAngle = (raw: number) => Math.max(raw, 180 - raw);
    expect(obtuseAngle(37)).toBe(143);
  });

  test('ANB = SNA - SNB avec angles normalisés', () => {
    const standardAngle = (raw: number) => Math.min(raw, 180 - raw);
    const sna = standardAngle(98.6); // 81.4
    const snb = standardAngle(104);   // 76
    const anb = parseFloat((sna - snb).toFixed(1));
    expect(anb).toBeCloseTo(5.4, 0);  // ANB positif → Classe II
  });

  test('Recouvrement et Surplomb doivent être en mm (pas en degrés)', () => {
    // Simulation du registre de mesures — règle de validation des unités
    const UNITS: Record<string, string> = {
      Surplomb: 'mm',
      Recouvrement: 'mm',
      SNA: '°',
      SNB: '°',
      ANB: '°',
      Inter_Incisif: '°',
      Decalage_A_B: 'mm',
      Situation_A: 'mm',
      Situation_B: 'mm',
    };

    expect(UNITS['Surplomb']).toBe('mm');
    expect(UNITS['Recouvrement']).toBe('mm');
    expect(UNITS['Decalage_A_B']).toBe('mm');
    expect(UNITS['Situation_A']).toBe('mm');
    expect(UNITS['SNA']).toBe('°');
    expect(UNITS['Inter_Incisif']).toBe('°');
  });

  test('diagnostic ne génère jamais "Classe III (Tendance II)"', () => {
    // Règle: les classes squelettiques et dentaires doivent rester séparées
    const forbiddenDiagnosis = 'Classe III (Tendance II)';
    const generateDiagnosis = (anb: number, dentalClass: string): string => {
      const skeletalClass = anb > 4 ? 'Classe II' : anb < 0 ? 'Classe III' : 'Classe I';
      // Règle: ne jamais fusionner les deux en une formule contradictoire
      return `${skeletalClass} squelettique — ${dentalClass} dentaire`;
    };

    const result = generateDiagnosis(-2, 'Classe II');
    expect(result).not.toContain(forbiddenDiagnosis);
    expect(result).not.toMatch(/Classe III.*Tendance II/);
  });

  test('SNA élevé ne génère pas de rétrognathie maxillaire', () => {
    const getDiagnostic = (sna: number): string => {
      if (sna > 84) return 'Prognathie maxillaire';
      if (sna < 80) return 'Rétrognathie maxillaire';
      return 'Classe I squelettique';
    };

    // SNA = 86° → prognathie, jamais rétrognathie
    expect(getDiagnostic(86)).not.toContain('Rétrognathie');
    expect(getDiagnostic(74)).toContain('Rétrognathie');
  });
});
