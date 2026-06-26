import { test, expect } from '@playwright/test';
import { mockAllApi, injectAuth, FAKE_TOKEN } from './helpers';

test.describe('Login flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockAllApi(page);
  });

  test('affiche le formulaire de connexion', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByText('Digital Crown AI')).toBeVisible();
    await expect(page.getByPlaceholder('nom@cabinet.com')).toBeVisible();
    await expect(page.getByPlaceholder('••••••••')).toBeVisible();
  });

  test('connexion réussie redirige vers /dashboard', async ({ page }) => {
    await page.goto('/login');

    await page.getByPlaceholder('nom@cabinet.com').fill('dentiste@test.com');
    await page.getByPlaceholder('••••••••').fill('password123');
    await page.getByRole('button', { name: /Se connecter/i }).click();

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  });

  test('identifiants incorrects affiche un message d\'erreur', async ({ page }) => {
    // Override login pour renvoyer 401
    await page.route('**/auth/login', (route) =>
      route.fulfill({
        status: 401,
        json: { detail: 'Identifiants incorrects.' },
      })
    );

    await page.goto('/login');
    await page.getByPlaceholder('nom@cabinet.com').fill('faux@email.com');
    await page.getByPlaceholder('••••••••').fill('mauvais_mdp');
    await page.getByRole('button', { name: /Se connecter/i }).click();

    await expect(page.getByText(/Identifiants incorrects/i)).toBeVisible({ timeout: 8_000 });
  });

  test('champs email et mot de passe sont requis', async ({ page }) => {
    await page.goto('/login');

    const btn = page.getByRole('button', { name: /Se connecter/i });
    await btn.click();

    // HTML5 validation empêche la soumission — le champ email doit avoir le focus
    const emailInput = page.getByPlaceholder('nom@cabinet.com');
    await expect(emailInput).toBeFocused();
  });

  test('bouton Créer un compte navigue vers /register', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /Créer un compte/i }).click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('déjà authentifié accède directement au dashboard', async ({ page }) => {
    // Inject a valid JWT token (year 2099) and navigate directly to protected route
    await injectAuth(page);
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  });
});
