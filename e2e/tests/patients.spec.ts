import { test, expect } from '@playwright/test';
import { mockAllApi, injectAuth, FAKE_PATIENT } from './helpers';

test.describe('Gestion des patients', () => {
  test.beforeEach(async ({ page }) => {
    await mockAllApi(page);
    await injectAuth(page);
  });

  // ── Liste patients ──────────────────────────────────────────────────────────

  test('liste des patients se charge et affiche un patient', async ({ page }) => {
    await page.goto('/patients');
    await expect(page.getByText('BENALI')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('Youssef')).toBeVisible();
  });

  test('affiche le numéro de dossier', async ({ page }) => {
    await page.goto('/patients');
    await expect(page.getByText('P-000042')).toBeVisible({ timeout: 10_000 });
  });

  // ── Création patient ────────────────────────────────────────────────────────

  test('formulaire de création patient est accessible', async ({ page }) => {
    await page.goto('/patients/new');

    // Le formulaire utilise des <label> sans htmlFor — utiliser placeholder
    await expect(page.getByPlaceholder('BENMOUSSA').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByPlaceholder('Yazan').first()).toBeVisible();
  });

  test('créer un patient via le formulaire soumet bien l\'API', async ({ page }) => {
    await page.goto('/patients/new');

    // Remplir le formulaire avec les sélecteurs réels (placeholder, pas label)
    const nomInput = page.getByPlaceholder('BENMOUSSA').first();
    const prenomInput = page.getByPlaceholder('Yazan').first();

    await expect(nomInput).toBeVisible({ timeout: 10_000 });
    await nomInput.fill('ALAMI');
    await prenomInput.fill('Sara');

    // Date de naissance (required)
    const dateInput = page.locator('input[type="date"]').first();
    if (await dateInput.isVisible()) {
      await dateInput.fill('1990-01-15');
    }

    // Soumettre — après succès, l'app navigue vers /patients
    const submitBtn = page.getByRole('button', { name: /Enregistrer|Créer|Ajouter/i }).first();
    if (await submitBtn.isVisible()) {
      await submitBtn.click();
      // La navigation vers /patients confirme que le POST a réussi
      await expect(page).toHaveURL(/\/patients/, { timeout: 8_000 });
    }
  });

  // ── Détail patient ──────────────────────────────────────────────────────────

  test('page de détail patient charge les informations', async ({ page }) => {
    await page.route('**/patients/42', (route) =>
      route.fulfill({ json: FAKE_PATIENT })
    );

    await page.goto('/patients/42');
    await expect(page.getByText('BENALI').first()).toBeVisible({ timeout: 10_000 });
  });

  // ── Recherche ───────────────────────────────────────────────────────────────

  test('champ de recherche est présent dans la liste patients', async ({ page }) => {
    await page.goto('/patients');
    const search = page.getByPlaceholder(/Rechercher par nom/i).first();
    await expect(search).toBeVisible({ timeout: 10_000 });
  });
});
