# P4 — Suivi Paiement / Échéancier : pré-audit statique

## Statut de preuve

Pré-cartographie **lecture seule** réalisée pendant les gates CI P2.

- **CODE VÉRIFIÉ** : oui, pour les constats ci-dessous.
- **TESTS EXÉCUTÉS P4** : non.
- **INTERACTION RUNTIME** : non exécutée.
- **CERTIFICATION FINANCIÈRE / PRODUCTION** : non revendiquée.

## P4-A — Génération rapide : arrondi non réconcilié

### Frontend vérifié
`InstallmentStudio` calcule :
`monthlyAmount = Math.round((totalAmount - advanceAmount) / monthsCount)`

Puis `generateTable()` crée chaque mensualité avec ce même montant arrondi.

### Risque
La somme `avance + mensualités` peut différer du total prévu. Le dernier versement n’est pas ajusté pour absorber l’écart.

### Décision recommandée
- calcul en centimes entiers ;
- répartir puis ajuster explicitement la dernière échéance ;
- afficher l’écart avant sauvegarde ;
- backend doit revalider la réconciliation exacte.

---

## P4-B — Contrat backend trop permissif

### Faits vérifiés
`backend/schemas/installments.py` n’impose actuellement :
- ni `total_amount > 0` ;
- ni `amount > 0` par échéance ;
- ni enum strict pour `status` ;
- ni somme des échéances = total du plan.

### Décision recommandée
Fail-closed au contrat, avec réconciliation monétaire exacte au centime et statuts explicitement autorisés.

---

## P4-C — Création du plan non atomique

### Fait vérifié
`POST /installments/` :
1. crée puis **commit** le `InstallmentPlan` ;
2. crée ensuite les lignes `Installment` ;
3. effectue un second commit.

### Risque
Une erreur pendant la création des échéances peut laisser un plan vide ou incomplet persisté.

### Décision recommandée
Une transaction unique : `add plan → flush → add installments → commit`, rollback complet sur échec.

---

## P4-D — Marquage PAYE invente le mode de règlement

### Fait vérifié
`PUT /installments/{id}` lorsqu’une échéance passe à `PAYE` crée automatiquement un `Payment` avec :
`payment_method = ESPECES`.

Le contrat `InstallmentUpdate` ne transporte aucun mode de paiement.

### Risque
La trésorerie peut enregistrer un paiement en espèces alors que le règlement réel était carte, chèque ou virement.

### Décision recommandée
- ne jamais inférer le mode de règlement ;
- soit exiger un mode explicite lors du passage à PAYE ;
- soit séparer mise à jour de l’échéance et encaissement via le flux paiement dédié.

---

## P4-E — Réouverture d’une échéance payée laisse le Payment actif

### Fait vérifié
Quand l’échéance passe de non payée à `PAYE`, un `Payment` est créé et lié par `installment_id`.

Si une requête ultérieure repasse le statut à `EN_ATTENTE` ou un autre statut, le code modifie seulement `inst.status`. Il ne supprime, n’annule ni ne neutralise le `Payment` précédemment créé.

### Risque
L’échéance peut apparaître non payée tandis que la trésorerie conserve encore l’encaissement correspondant.

### Décision recommandée
Définir une transition financière atomique et réversible : soit refuser la réouverture après encaissement sans opération d’annulation explicite, soit créer une vraie contre-écriture/annulation auditée. Ne jamais simplement changer le statut.

---

## P4-F — Montant modifié pendant le passage à PAYE : ordre incohérent

### Fait vérifié
Dans `update_installment`, le `Payment` est créé avec `amount=inst.amount` **avant** l’application éventuelle de `req.amount` sur l’échéance.

### Risque
Une requête unique `{status: PAYE, amount: nouveau_montant}` peut créer un Payment avec l’ancien montant puis enregistrer l’échéance avec le nouveau montant.

### Décision recommandée
Valider/appliquer d’abord les champs financiers dans une transaction contrôlée, puis créer l’encaissement à partir de l’état final validé.

---

## P4-G — Preview dédiée

### Fait vérifié
Le flux actif échéancier de `useDocumentGenerator.handleGenerate()` utilise `params.echeancierPayload` et appelle `/installments/generate-preview`.

Le vieux branchement DOM `data-plan-data` dans `buildPayload()` n’est pas utilisé par ce chemin actif.

`/installments/generate-preview` génère uniquement le PDF et ne persiste pas de plan/paiement dans le code inspecté.

### Conclusion
Le mismatch camelCase du vieux `data-plan-data` est une dette de code mort, **pas un bug du flux actif**.

---

## P4-H — Points restant à cartographier

- suppression/modification d’un plan déjà existant ;
- doublons d’encaissement lors de transitions répétées ;
- rappels WhatsApp et normalisation téléphone ;
- résumé payé/restant/prochaine échéance ;
- tests runtime et régression financière ciblée.
