  let responsePromise = page.waitForResponse(response => response.url().includes('/api/documents/generate') && response.request().method() === 'POST', { timeout: 30000 });
  await page.getByRole('button', { name: 'Enregistrer', exact: true }).click();
  if (!(await responsePromise).ok()) throw new Error('certificate save failed');
  await freeCertificate.fill(`Contenu certifié G4 navigateur impression ${viewport.width}x${viewport.height}`);
  responsePromise = page.waitForResponse(response => response.url().includes('/api/documents/generate') && response.request().method() === 'POST', { timeout: 30000 });
  await page.getByRole('button', { name: 'Préparer impression', exact: true }).click();
  if (!(await responsePromise).ok()) throw new Error('certificate prepare print failed');
  actions.push('certificate-save-prepare-print');
  const certScene = await snap(page, viewport, 'certificate');

  await page.goto(base + 'echeancier', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Suivi Paiement', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await exerciseStudioHeader(page);
  await page.getByRole('button', { name: 'Nouveau plan', exact: true }).click();
  const title = page.getByPlaceholder('Ex: Plan de paiement');
  await title.fill('Plan G4 navigateur');
  await (await fieldAfter(page, 'Montant Total Prévu (MAD)')).fill('1000');
  await (await fieldAfter(page, 'Avance (MAD)')).fill('200');
  await (await fieldAfter(page, 'Date Avance')).fill('2026-10-03');
  await (await fieldAfter(page, 'Nbre Mensualités')).fill('2');
  await page.getByRole('button', { name: /Générer le tableau des échéances/i }).click();
  await page.locator('input[value="Avance Initiale"]').waitFor({ state: 'visible', timeout: 5000 });
  await page.locator('input[value="Mensualité 1"]').waitFor({ state: 'visible', timeout: 5000 });
  await page.locator('input[value="Mensualité 2"]').waitFor({ state: 'visible', timeout: 5000 });
  await page.getByText('Total équilibré', { exact: true }).waitFor({ state: 'visible', timeout: 5000 });
  actions.push('installment-generate');

  await page.getByRole('button', { name: /Ajouter manuellement/i }).click();
  const manualRow = page.locator('input[value="Nouveau versement"]');
  await manualRow.waitFor({ state: 'visible' });
  await page.getByRole('button', { name: /Supprimer Nouveau versement/i }).click();
  if (await page.locator('input[value="Nouveau versement"]').count()) throw new Error('manual installment deletion failed');
  actions.push('installment-manual-add-remove');

  const save = page.getByRole('button', { name: 'Enregistrer le plan', exact: true });
  await save.waitFor({ state: 'visible' });
  if (await save.isDisabled()) throw new Error('balanced plan save remained disabled');
  await save.click();
  await page.getByText(/Plan enregistré #/).waitFor({ state: 'visible', timeout: 15000 });
  actions.push('installment-save');

  const firstMethod = page.locator('select[aria-label^="Mode de règlement"]').first();
  await firstMethod.selectOption('CARTE');
  const collect = page.getByRole('button', { name: 'Encaisser', exact: true }).first();
  if (await collect.isDisabled()) throw new Error('collect remained disabled after method selection');
  const collectResponsePromise = page.waitForResponse(
    response => /\/api\/installments\/\d+$/.test(new URL(response.url()).pathname) && response.request().method() === 'PUT',
    { timeout: 30000 },
  );
  await collect.click();
  const collectResponse = await collectResponsePromise;
  if (!collectResponse.ok()) throw new Error('installment collection request failed');
  const collectBody = await collectResponse.json();
  if (collectBody?.status !== 'PAYE') throw new Error('installment collection ACK is not PAYE');
  await page.getByText('PAYÉ', { exact: true }).first().waitFor({ state: 'visible', timeout: 30000 });
  actions.push('installment-collect');

  const reminder = page.locator('input[aria-label^="Activer rappel WhatsApp"]').last();
  await reminder.check();
  const wa = page.getByTitle('Ouvrir WhatsApp avec le rappel prérempli');
  await page.evaluate(() => {
    window.__g4OpenedUrl = null;
    window.open = (url) => { window.__g4OpenedUrl = String(url || ''); return null; };
  });
  await wa.click();
  const openedUrl = await page.evaluate(() => window.__g4OpenedUrl);
  if (!openedUrl || !openedUrl.startsWith('https://wa.me/')) throw new Error('WhatsApp reminder URL not produced');
  actions.push('installment-reminder');
  await exercisePreview(page);
  actions.push('installment-preview');
  responsePromise = page.waitForResponse(response => response.url().includes('/api/installments/generate-preview') && response.request().method() === 'POST', { timeout: 30000 });
  await page.getByRole('button', { name: 'Enregistrer', exact: true }).click();
  const installmentGenerateResponse = await responsePromise;
  if (!installmentGenerateResponse.ok()) throw new Error('installment footer generation failed');
  actions.push('installment-footer-enregistrer-is-preview-only');
  await page.getByRole('button', { name: 'Imprimer', exact: true }).click();
  const warning = page.getByRole('dialog', { name: 'Attention : Impression Directe' });
  await warning.waitFor({ state: 'visible', timeout: 5000 });
  await warning.getByRole('button', { name: 'Annuler', exact: true }).click();
  await page.getByRole('button', { name: 'Imprimer', exact: true }).click();
  await warning.waitFor({ state: 'visible', timeout: 5000 });
  responsePromise = page.waitForResponse(response => response.url().includes('/api/installments/generate-preview') && response.request().method() === 'POST', { timeout: 30000 });
  await warning.getByRole('button', { name: 'Confirmer', exact: true }).click();
  if (!(await responsePromise).ok()) throw new Error('installment print confirmation failed');
  actions.push('installment-save-print');
  const installmentScene = await snap(page, viewport, 'installment');

  await page.goto(base + 'libre', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Document Libre', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await closeResidualPreview(page);
  await exerciseStudioHeader(page);
  await page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...').fill('Lettre G4');
  await page.getByPlaceholder('Ex: À qui de droit...').fill('À qui de droit');
  await page.getByPlaceholder('Ex: Rabat, le 12/05/2026').fill('Rabat, le 19/09/2026');
  await page.getByLabel(/Masquer l'en-tête patient/i).check();
  for (const name of ['A5','A4','Gauche','Centre','Droite','Justifié']) await page.getByRole('button', { name, exact: true }).click();
  const content = page.getByPlaceholder("Rédigez votre document ici... Utilisez la barre d'outils pour mettre en forme le texte.");
  await content.fill('Texte G4');
  for (const [titleName, token] of [['Gras','<b>'],['Italique','<i>'],['Souligné','<u>'],['Agrandir','<font size="16">']]) {
    await content.evaluate(el => { el.selectionStart = 0; el.selectionEnd = el.value.length; });
    await page.getByTitle(titleName).click();
    await page.waitForTimeout(30);
    if (!(await content.inputValue()).includes(token)) throw new Error('libre format failed: ' + titleName);
  }
  await page.getByTitle('Tableau').click();
  if (!(await content.inputValue()).includes('| Colonne 1 |')) throw new Error('libre table insertion failed');
  actions.push('libre-residual-controls');
  await exercisePreview(page);
  actions.push('libre-preview-refresh-close');