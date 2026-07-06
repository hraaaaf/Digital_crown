# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> Login flow >> affiche le formulaire de connexion
- Location: tests\login.spec.ts:9:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByPlaceholder('â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 8000ms
  - waiting for getByPlaceholder('â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢')

```

```yaml
- img "Digital Crown"
- heading "Digital Crown AI" [level=1]
- paragraph: Connectez-vous à votre espace
- text: Email Professionnel
- textbox "nom@cabinet.com"
- text: Mot de passe
- textbox "••••••••"
- checkbox "Rester connecté" [checked]
- text: Rester connecté
- button "Se connecter"
- paragraph:
  - text: Nouveau sur Digital Crown ?
  - button "Créer un compte"
- text: Ou continuer avec
- button "Google":
  - img
  - text: Google
- paragraph: © 2026 SANINOVA - Digital Crown Elite Edition v4.0
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import { mockAllApi, injectAuth } from './helpers';
  3  | 
  4  | test.describe('Login flow', () => {
  5  |   test.beforeEach(async ({ page }) => {
  6  |     await mockAllApi(page);
  7  |   });
  8  | 
  9  |   test('affiche le formulaire de connexion', async ({ page }) => {
  10 |     await page.goto('/login');
  11 |     await expect(page.getByText('Digital Crown AI')).toBeVisible();
  12 |     await expect(page.getByPlaceholder('nom@cabinet.com')).toBeVisible();
> 13 |     await expect(page.getByPlaceholder('â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢')).toBeVisible();
     |                                                                     ^ Error: expect(locator).toBeVisible() failed
  14 |   });
  15 | 
  16 |   test('visiteur non authentifie sur / est redirige vers /landing', async ({ page }) => {
  17 |     await page.addInitScript(() => {
  18 |       localStorage.clear();
  19 |       sessionStorage.clear();
  20 |     });
  21 | 
  22 |     await page.goto('/');
  23 |     await expect(page).toHaveURL(/\/landing/, { timeout: 10_000 });
  24 |   });
  25 | 
  26 |   test('utilisateur authentifie sur / est redirige vers /dashboard', async ({ page }) => {
  27 |     await injectAuth(page);
  28 |     await page.goto('/');
  29 |     await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  30 |   });
  31 | 
  32 |   test('connexion reussie redirige vers /dashboard', async ({ page }) => {
  33 |     await page.goto('/login');
  34 | 
  35 |     await page.getByPlaceholder('nom@cabinet.com').fill('dentiste@test.com');
  36 |     await page.getByPlaceholder('â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢').fill('password123');
  37 |     await page.getByRole('button', { name: /Se connecter/i }).click();
  38 | 
  39 |     await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  40 |   });
  41 | 
  42 |   test('identifiants incorrects affiche un message d\'erreur', async ({ page }) => {
  43 |     await page.route('**/auth/login', (route) =>
  44 |       route.fulfill({
  45 |         status: 401,
  46 |         json: { detail: 'Identifiants incorrects.' },
  47 |       })
  48 |     );
  49 | 
  50 |     await page.goto('/login');
  51 |     await page.getByPlaceholder('nom@cabinet.com').fill('faux@email.com');
  52 |     await page.getByPlaceholder('â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢').fill('mauvais_mdp');
  53 |     await page.getByRole('button', { name: /Se connecter/i }).click();
  54 | 
  55 |     await expect(page.getByText(/Identifiants incorrects/i)).toBeVisible({ timeout: 8_000 });
  56 |   });
  57 | 
  58 |   test('champs email et mot de passe sont requis', async ({ page }) => {
  59 |     await page.goto('/login');
  60 | 
  61 |     const btn = page.getByRole('button', { name: /Se connecter/i });
  62 |     await btn.click();
  63 | 
  64 |     const emailInput = page.getByPlaceholder('nom@cabinet.com');
  65 |     await expect(emailInput).toBeFocused();
  66 |   });
  67 | 
  68 |   test('bouton Creer un compte navigue vers /register', async ({ page }) => {
  69 |     await page.goto('/login');
  70 |     await page.getByRole('button', { name: /CrÃ©er un compte/i }).click();
  71 |     await expect(page).toHaveURL(/\/register/);
  72 |   });
  73 | 
  74 |   test('deja authentifie accede directement au dashboard', async ({ page }) => {
  75 |     await injectAuth(page);
  76 |     await page.goto('/dashboard');
  77 |     await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  78 |   });
  79 | });
  80 | 
```