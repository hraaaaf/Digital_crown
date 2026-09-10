# P5 — Suivi Paiement : audit canonique exhaustif

## Baseline

- Branche audit : `agent/p4-p6-audit-baselines`.
- Baseline source : `master` à `026f78290cda53ea1b07ba5e8bfd39836448d6ce`.
- Portée : `InstallmentStudio`, plans/échéances, génération, édition, passage payé, mode de règlement, rappels WhatsApp, preview/PDF et connexions P3/P4.
- **CODE VÉRIFIÉ** : oui pour les constats ci-dessous.
- **TESTS HISTORIQUES EXÉCUTÉS** : anciens P4-A/P4-B certifiés par CI exacte selon la roadmap.
- **TEST EXÉCUTÉ SUR CET AUDIT** : non revendiqué à la date du baseline ; voir certification finale ci-dessous.
- **INTERACTION RUNTIME / VISUELLE** : non exécutée au baseline ; voir certification finale ci-dessous.
- **CERTIFICATION FINANCIÈRE / PRODUCTION** : non revendiquée au baseline.

---

## 1. Architecture réelle P5

Flux principal :

`InstallmentStudio.tsx` → payload parent / `/installments/*` ou génération document `echeancier` → modèles `InstallmentPlan` / `Installment` → passage PAYE via `PUT /installments/{id}` → création `Payment` lié à `installment_id`.

Sous-flux : génération rapide, ajout manuel, édition montant/date/libellé, chargement du dernier plan, rappel WhatsApp manuel, preview PDF.

---

## 2. Matrice produit

### GARDER

1. Contrôle permission `accounting` + isolation patient sur lecture/création/mutation.
2. Répartition automatique exacte au centime dans `buildExactInstallmentAllocation()`.
3. Une échéance déjà PAYE ne peut plus être rouverte ou rechiffrée sans contrepassation.
4. Passage vers PAYE exige une méthode de règlement.
5. Le `Payment` créé lors du passage PAYE est lié à `installment_id`.
6. Rappel WhatsApp réellement manuel : ouverture explicite de `wa.me`, pas d'envoi automatique caché.
7. Preview peut être générée sans persister lorsqu'elle passe par le chemin preview du générateur documentaire.

### AMÉLIORER

1. État initial neutre : `Traitement Orthodontique` est prérempli alors que P5 est généraliste.
2. « Montant / Mois » est éditable mais, lorsque `totalAmount > 0`, la génération recalcule les montants et ignore cette saisie comme source financière.
3. Chargement du « dernier plan » doit être rendu explicite si plusieurs plans existent.
4. Résumé financier doit distinguer payé / restant / prochaine échéance et source de vérité serveur.
5. Responsive tableau 390/768 à certifier ; sur petit écran six colonnes sont susceptibles d'être difficiles à exploiter.

### CORRIGER — P0

#### P0-1 — création directe d'un plan sans réconciliation serveur
`InstallmentPlanCreate` accepte `total_amount` et une liste d'échéances sans validator imposant que la somme des montants égale le total. `POST /installments/` persiste ces valeurs directement.

**Conséquence** : un appel direct ou un frontend modifié peut créer un plan financièrement incohérent malgré l'allocation exacte disponible dans l'UI.

**Décision** : appliquer la même réconciliation exacte au centime côté backend avant toute écriture.

#### P0-2 — montants/statuts d'échéance insuffisamment bornés au contrat direct
`InstallmentBase.amount` est un `float` sans contrainte positive/finie et `status` est un `str` libre. Le create direct ne ferme pas ces valeurs.

**Conséquence** : échéances négatives/nulles ou statuts arbitraires peuvent entrer dans le modèle depuis le contrat direct.

**Décision** : montant strictement positif, valeur finie, statut fermé, dates valides, titre/libellé bornés.

#### P0-3 — chemin document `echeancier` direct persiste avant contrat financier complet
Dans `/documents/generate`, le chemin `echeancier` sans `plan_id` construit directement `InstallmentPlan` et les lignes à partir de `req.data`, sans modèle P5 dédié ni réconciliation total/lignes avant persistance.

**Décision** : une seule politique financière P5 partagée par `/installments/`, génération document et preview.

### CORRIGER — P1

#### P1-1 — checkbox « Réglé » locale ≠ encaissement comptable
Dans `InstallmentStudio`, cocher `paid` modifie l'état local/payload de preview. Le vrai passage PAYE comptable exige le `PUT /installments/{id}` avec méthode de règlement.

**Risque UX** : l'utilisateur peut croire qu'une échéance est encaissée alors qu'il ne s'agit que d'un état de brouillon/preview.

**Décision** : distinguer clairement « afficher comme réglé dans le brouillon » et « enregistrer un paiement », idéalement supprimer l'ambiguïté et déclencher le workflow comptable explicite.

#### P1-2 — édition manuelle peut déséquilibrer le plan
Après génération exacte, l'utilisateur peut modifier librement montants ou supprimer/ajouter des lignes. L'UI affiche seulement un avertissement `Total planifié diffère du total prévu`; aucune barrière visible dans ce composant n'empêche le parent de recevoir le payload déséquilibré.

**Décision** : blocage save/archive tant que non réconcilié, doublé d'une validation serveur.

#### P1-3 — chargement implicite du dernier plan
Le composant charge `plans[plans.length - 1]` sans sélection explicite ni preuve d'ordre serveur contractuel.

**Décision** : endpoint « active/latest » explicite avec tri serveur déterministe, ou sélecteur de plan.

#### P1-4 — fallback de date lors de génération documentaire
Le chemin `echeancier` peut retomber sur la date courante lorsque `dueDate` manque.

**Décision** : une échéance persistée doit avoir une date explicite valide ; pas d'invention de date financière.

---

## 3. Contrat cible P5

Un plan persistant doit satisfaire simultanément :
- patient autorisé ;
- titre non vide et borné ;
- total fini et strictement positif ;
- au moins une échéance ;
- chaque montant fini et strictement positif ;
- somme exacte des échéances = total au centime ;
- statut dans un enum fermé ;
- date explicite ;
- passage PAYE transactionnel avec méthode de règlement explicite ;
- Payment unique lié à l'échéance ;
- aucune réouverture/revalorisation d'une échéance payée sans contrepassation.

---

## 4. Connexions inter-pages

| Connexion | État code | Verdict |
|---|---|---|
| P4 → P5 | note globale peut créer un plan | **GARDER**, contrat exact déjà partiellement présent |
| P5 → P3 | état d'échéancier historiquement partagé | **ISOLER** : aucun transfert implicite dans Devis |
| P5 → comptabilité | Payment lié à installment | **GARDER** |
| P5 → WhatsApp | ouverture manuelle | **GARDER**, expliciter absence d'envoi automatique |
| P5 → PDF | preview/génération | **RECERTIFIER** |

---

## 5. Lots correctifs canoniques

1. **P5-A — Contrat serveur unique** : montants/statuts/dates/titre + réconciliation exacte sur tous les endpoints.
2. **P5-B — Encaissement explicite** : supprimer ambiguïté checkbox locale vs vrai paiement.
3. **P5-C — Lifecycle des plans** : latest/actif déterministe, sélection, contrepassation.
4. **P5-D — Édition et sauvegarde** : fail-closed si déséquilibre, aucune date inventée.
5. **P5-E — Rappels / résumé financier** : états réels, WhatsApp manuel explicite.
6. **P5-F — PDF / responsive / accessibilité**.
7. **P5-G — Recertification financière finale**.

---

## 6. Gates runtime du baseline

- création plan exact / sous-alloué / sur-alloué ;
- zéro/négatif/NaN/valeur extrême ;
- ajout/suppression/édition manuelle ;
- plusieurs plans et sélection du dernier ;
- passage PAYE avec/sans méthode ;
- tentative de réouverture/rechiffrage d'un PAYE ;
- rapprochement Payment ↔ échéance ;
- rappel WhatsApp avec/sans téléphone ;
- preview non persistante ;
- archive/génération persistante ;
- responsive 390/768/1280 et clavier.

---

## 7. Certification finale engineering — 2026-09-10

Branche : `cert/p5-runtime-financial`.
PR : `#402`.
Base post-Cephalo : `6dcdb18d364545a151f1e2a3fa01b1ce37a9494f`.
HEAD certifié avant closeout documentaire : `63d33c2c926120fec45174aba831c1154e48b35a`.

### Runtime / financier vérifié

- CI principal `#3156` / run `34520821875` : **success** sur le HEAD ci-dessus.
- T2 Runtime Browser Certification `#2167` / run `34520821872` : **success** sur le même HEAD.
- Settings R11 `#495` : **success** ; Patient P7 Final Certification `#1184` : **success**.
- Probe financier T2 : **PASS** ; P5 plan `1200.0`, échéances `500.0 + 700.0`, encaissé `500.0`.
- Preview financière certifiée non persistante par les tests runtime ciblés de la PR.
- Sélection `latest` certifiée déterministe : `created_at DESC`, puis `id DESC` à égalité.
- Une échéance `PAID/PAYE` ne peut être rechiffrée ni rouverte sans sémantique de contrepassation explicite.
- Aucune nouvelle primitive de contrepassation n'est introduite par P5 ; ce scénario comptable reste un lot séparé.

### PDF / navigateur vérifié

Artefact AFTER : `t2-browser-evidence` du run T2 `#2167`.

- matrice réelle : `390x844`, `430x932`, `768x1024`, `1280x900` + double-check dark `1280x900` ;
- Suivi Paiement : **10/10 automatisé** sur navigation, contenu, actions, overflow responsive, stabilité runtime, hiérarchie/lisibilité et preview ;
- `scrollWidth == clientWidth` sur les viewports certifiés : aucun overflow horizontal document ;
- preview Escape : PASS ;
- impression navigateur : PASS via PDF blob → iframe cachée → focus → print ;
- fraîcheur PDF : PASS, hash différent après changement de contenu et payload le plus récent observé.

### Comparaison visuelle humaine BEFORE → AFTER

BEFORE : run T2 `#2166` / SHA `06d76834b88e22c06b55db80071d2c13b7ab4371`.
AFTER : run T2 `#2167` / SHA `63d33c2c926120fec45174aba831c1154e48b35a`.

Même viewports inspectés : `390`, `768`, `1280`.

Constats :
- structure et workflow conservés ;
- commandes d'encaissement visiblement plus hautes et plus faciles à cibler aux viewports 768/1280 ;
- densité mobile réduite sans créer d'overflow horizontal ;
- aucune coupure nouvelle ni régression de hiérarchie observée ;
- le mobile 390 reste structurellement dense, mais l'AFTER n'aggrave pas la composition et le gate d'overflow reste vert.

**Score visuel humain P5 AFTER : 8,8/10.**

Ce score n'est pas le score automatisé T2 10/10 : il reflète l'inspection esthétique/ergonomique humaine des captures, avec réserve sur la densité du viewport 390.

## 8. Verdict

**P5 engineering/runtime automatisé : ✅ certifié sur `63d33c2c...` avant le commit documentaire de closeout.**

Restent hors de cette certification :
- validation comptable/réglementaire humaine si exigée ;
- définition métier d'une vraie contrepassation comptable ;
- validation sur un cabinet réel / production locale réelle.

Tout nouveau commit de closeout documentaire doit repasser les checks requis avant merge ; il ne modifie pas le comportement financier certifié sauf diff contraire.