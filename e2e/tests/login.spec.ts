import { test, expect } from '@playwright/test';
import { mockAllApi, injectAuth } from './helpers';

test.describe('Login flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockAllApi(page);
  });

  test('affiche le formulaire de connexion', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByText('Digital Crown AI')).toBeVisible();
    await expect(page.getByPlaceholder('nom@cabinet.com')).toBeVisible();
    await expect(page.getByPlaceholder('â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢')).toBeVisible();
  });

  test('visiteur non authentifie sur / est redirige vers /landing', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    await page.goto('/');
    await expect(page).toHaveURL(/\/landing/, { timeout: 10_000 });
  });

  test('utilisateur authentifie sur / est redirige vers /dashboard', async ({ page }) => {
    await injectAuth(page);
    await page.goto('/');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  });

  test('connexion reussie redirige vers /dashboard', async ({ page }) => {
    await page.goto('/login');

    await page.getByPlaceholder('nom@cabinet.com').fill('dentiste@test.com');
    await page.getByPlaceholder('â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢').fill('password123');
    await page.getByRole('button', { name: /Se connecter/i }).click();

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  });

  test('identifiants incorrects affiche un message d\'erreur', async ({ page }) => {
    await page.route('**/auth/login', (route) =>
      route.fulfill({
        status: 401,
        json: { detail: 'Identifiants incorrects.' },
      })
    );

    await page.goto('/login');
    await page.getByPlaceholder('nom@cabinet.com').fill('faux@email.com');
    await page.getByPlaceholder('â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢').fill('mauvais_mdp');
    await page.getByRole('button', { name: /Se connecter/i }).click();

    await expect(page.getByText(/Identifiants incorrects/i)).toBeVisible({ timeout: 8_000 });
  });

  test('champs email et mot de passe sont requis', async ({ page }) => {
    await page.goto('/login');

    const btn = page.getByRole('button', { name: /Se connecter/i });
    await btn.click();

    const emailInput = page.getByPlaceholder('nom@cabinet.com');
    await expect(emailInput).toBeFocused();
  });

  test('bouton Creer un compte navigue vers /register', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /CrÃ©er un compte/i }).click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('deja authentifie accede directement au dashboard', async ({ page }) => {
    await injectAuth(page);
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  });
});
