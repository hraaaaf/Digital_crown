# Document Studio — roadmap canonique page par page

## Objectif

Auditer, corriger et recertifier le Studio documentaire de Digital Crown **page par page**, sans confondre code vérifié, tests exécutés, runtime observé et certification métier.

Ordre canonique actuel :

1. **P1 — Ordonnance**
2. **P2 — Certificat**
3. **P3 — Devis**
4. **P4 — Note Honoraires**
5. **P5 — Suivi Paiement**
6. **P6 — Document Libre**
7. **P7 — Compagnon Diagnostique** : identifiant historique conservé, mais surface **retirée du Studio certifiable actuel** et code dormant
8. **T1 — Audit transversal premium**
9. **T2 — Refonte intelligente finale / recertification globale**

Les anciens identifiants techniques restent conservés dans les PR/commits/audits historiques.

## Règle de preuve

- **CODE VÉRIFIÉ** : démontré par source/diff.
- **TEST EXÉCUTÉ** : réellement lancé avec résultat observé.
- **INTERACTION EXÉCUTÉE** : observée dans l’application réelle.
- **CERTIFICATION CLINIQUE / FINANCIÈRE / PRODUCTION** : indépendante de l’engineering.

Une CI qui échoue avant tout step n’est ni un échec du code ni un PASS.

---

## P1 — Ordonnance

**État : ✅ engineering fermé + recertification visuelle réalisée ; gates authentifiés/cliniques séparés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md`.

Acquis : R1→R7 fusionnés, safety fail-closed, dirty-state, habitudes/protocoles, UX rapide, contexte patient, preview responsive, visuel 1440/768/390.

Reste : interaction authentifiée locale et certification clinique/pharmacologique humaine.

---

## P2 — Certificat

**État : ✅ engineering convergé ; ⏳ certification finale runtime/PDF non fermée.**

Rapport historique : `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md`.

Acquis : nature explicite, dates/durée séparées, aucun choix clinique prérempli, texte libre praticien, contrat backend, signature manuscrite dentiste, impression fraîche, intégrité PDF, QR neutralisé sans contrat valide.

Reste : régression finale, runtime authentifié, inspection PDF et certification réglementaire/clinique si requise.

---

## P3 — Devis

**État : 🟡 P3-A→P3-G intégrés sur PR #77 ; P3-H partiellement exécuté ; PR toujours draft/non mergée.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_INTEGRATION_STATUS.md` sur la branche P3.

Acquis sur #77 : isolation financière Devis, source de vérité odontogramme, catalogue/dentition, phases non financières, apprentissage autoritatif, Plan→Devis, suppression suggestion RDV financière générique, PDF multipage lisible, responsive/accessibilité engineering.

Preuves ciblées historiques P3-H : backend 13 passed ; policies frontend 22 groupes ; odontogramme 9 groupes ; PriceBrain 1 groupe ; PDF long 36 actes → 3 pages avec en-tête répété et minimum observé 7,5 pt.

Reste : suite complète + build, smoke authentifié, PDF cabinet réel, responsive réel, merge et post-merge.

---

## P4 — Note Honoraires

**État : ✅ engineering + runtime automatisé fermés sur PR #386 ; validations comptable/réglementaire humaine et production réelle séparées.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P4_HONORAIRES_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_FINAL_CERTIFICATION_2026-09-09.md`.

HEAD produit certifié : `99c63b1247448805360e949d6da745afa53ba340`.

### Engineering acquis

- contrats Devis P3 et Honoraires P4 fusionnés sans régression volontaire ;
- statut documentaire fermé ; `PARTIEL` refusé sans montant encaissé explicite ;
- note/acte vide refusés ; montants finis, >0, ≤ 1 000 000 MAD ;
- validation request + pré-PDF + persistance ;
- `PAYE` exige un mode de règlement choisi explicitement ;
- `EN_ATTENTE` n’exige, ne sérialise et ne conserve aucun mode de règlement ;
- aucun fallback silencieux vers Espèces à la persistance ;
- allocation exacte `Acte ↔ Payment` conservée ;
- note globale réconciliée au centime ;
- échéances d’une note exigeant un plan datées explicitement avant PDF/archive : aucune date financière synthétisée ;
- Devis → Honoraires conserve les actes mais réinitialise statut/mode/plan/échéances ;
- aucun historique P5 injecté dans le store P3/P4 ;
- suggestions radio/RDV non contractuelles retirées du parcours financier ;
- édition remplace l’archive logique au lieu d’ajouter un doublon ;
- réouverture réhydrate `payment_status` et `is_accounted` ;
- corbeille/restauration et agrégats financiers actifs durcis ;
- tests request, pré-PDF, persistance, absence d’inférence clinique et store ajoutés.

### Certification observée

- T2 Runtime Browser run `34413159443` : **success** ;
- CI principal run `34413159336` : **success** ;
- invalides P4 422 sans mutation DB : note vide, montant 0, PAYE sans mode, PARTIEL implicite ;
- EN_ATTENTE : Acte sans Payment ;
- PAYE : Acte + Payment exact lié à `acte_id` ;
- multi-actes PAYE : 2 Actes + 2 Payments exacts ;
- note globale : équilibre exact accepté, déséquilibres refusés ;
- archive/relecture : statut PAYE et `is_accounted=true` conservés ;
- navigateur Honoraires vert sur 390/430/768/1280 + dark 1280 ;
- preview, PDF runtime, impression navigateur et fraîcheur PDF : verts dans T2 ;
- PR #384/#385 : édition/archives/comptabilité/Historique et dropdown visuel certifiés puis mergés.

### Hors périmètre engineering

- validation comptable/réglementaire humaine si exigée ;
- inspection esthétique humaine d’un PDF cabinet réel ;
- certification production sur environnement cabinet réel.

Ces validations externes ne rouvrent pas P4 engineering sauf défaut observé.

---

## P5 — Suivi Paiement

**État : ✅ engineering + runtime/PDF/responsive automatisés certifiés sur PR #402 ; contrepassation comptable et validations humaines séparées.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md`.

### Engineering acquis

- création/preview/mutation fail-closed : titre, total, lignes, dates, montants, statuts ;
- réconciliation exacte au centime ;
- endpoint `latest` explicite, tri déterministe `created_at DESC, id DESC` ;
- échéance PAYE non réouvrable/non rechiffrable sans contrepassation ;
- plan encaissé non supprimable sans contrepassation ;
- UI `brouillon → équilibre → enregistrement → encaissement` ;
- ancien checkbox local « Réglé » supprimé ;
- aucun mode de paiement présélectionné ;
- bouton d’encaissement désactivé jusqu’au choix explicite ;
- montants persistés figés ; restructuration via nouveau plan ;
- résumé total/payé/restant ;
- WhatsApp manuel uniquement ;
- P5 charge son propre `/latest` et ne pollue plus le store P3/P4 ;
- cibles tactiles principales ≥44 px et focus clavier visible ;
- tests schema, route et frontend ajoutés/alignés.

### Certification observée

HEAD comportemental certifié avant closeout documentaire : `63d33c2c926120fec45174aba831c1154e48b35a`.

- CI principal `#3156` / run `34520821875` : **success** ;
- T2 Runtime Browser `#2167` / run `34520821872` : **success** ;
- plan P5 runtime : total `1200.0`, lignes `500.0 + 700.0`, encaissé `500.0` ;
- preview financière non persistante, latest déterministe et immutabilité PAYE couverts par la certification runtime ciblée ;
- navigateur P5 vert sur 390/430/768/1280 + dark 1280 ; aucun overflow horizontal document ;
- preview Escape, impression navigateur et fraîcheur PDF : PASS ;
- comparaison humaine BEFORE `#2166` → AFTER `#2167` aux viewports 390/768/1280 : structure conservée, contrôles d'encaissement plus confortables, aucune régression visuelle nouvelle ;
- score visuel humain AFTER : **8,8/10**, réserve principale = densité structurelle au viewport 390.

### Hors périmètre engineering

- définition et certification d'une vraie contrepassation comptable ;
- validation comptable/réglementaire humaine si exigée ;
- validation sur cabinet réel / production locale réelle.

Ces points ne rouvrent pas P5 engineering sauf défaut observé.

---

## P6 — Document Libre

**État : ✅ engineering + CI + runtime/PDF/responsive certifiés, PR #405 mergée et `master` vérifié.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P6_DOCUMENT_LIBRE_AUDIT.md` ;
- historique `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md` ;
- statut stack : `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md`.

HEAD comportemental certifié : `218e7ef1580e69958f02d9e8319750772f273376`.
HEAD closeout exact : `9269f9c4111b1c7ce58dfcaa748b4b56cf892b13`.
Merge squash sur `master` : `e5a9f37fe33690759124cadb18d672d756647578`.

### Engineering acquis

- validation titre/contenu, toolbar non-submit, contrat/PDF sûr et allowlist markup ;
- caractères spéciaux et balises déséquilibrées rendus sûrs ;
- document long/multipage lisible, tableaux Markdown et formats A4/A5 ;
- destinataire/date personnalisés, alignements et masquage d'en-tête ;
- impression depuis un PDF frais ;
- auto-preview invalide silencieux, dirty-state, permission clinique et archive/réouverture ;
- probe P6 authentifié dédié aux contrôles éditeur 390/768/1280 sans changement produit.

### Certification observée

- HEAD comportemental : CI `#3183` / `34528255939` **success** ; T2 `#2191` / `34528255978` **success** ;
- HEAD closeout exact : CI `#3224` / `34582263330` **success** ; T2 `#2229` / `34582263341` **success** ;
- T2 : strict runtime PDF, matrice navigateur authentifiée, probe P6 et fraîcheur print/PDF **success** ;
- frontend CI : test suite + build **success** ;
- captures P6 dédiées 390x844, 768x1024 et 1280x900 : PASS, aucun overflow document ni clipping des contrôles ciblés ;
- inspection humaine : aucune régression visuelle bloquante ; score visuel **9/10**, réserve principale = densité mobile non bloquante ;
- post-merge : branche `master` vérifiée exactement à `e5a9f37...` avec le squash P6.

### Hors périmètre engineering

- WYSIWYG et bibliothèque de templates : améliorations produit réversibles, pas gates de sécurité ;
- certification production sur un cabinet réel ;
- validation réglementaire humaine si elle devient requise pour un usage donné.

Ces points ne rouvrent pas P6 engineering sauf défaut observé.

---

## P7 — Compagnon Diagnostique

**État actuel : ⛔ surface retirée du Document Studio certifiable ; code historique dormant ; aucune certification runtime/scientifique active revendiquée.**

Rapports :
- vérité produit actuelle : `docs/audits/DOCUMENT_STUDIO_P7_CURRENT_PRODUCT_TRUTH_2026-09-11.md` ;
- historique : `docs/audits/DOCUMENT_STUDIO_P7_COMPAGNON_DIAGNOSTIQUE_AUDIT.md` ;
- historique d’intégration : `docs/audits/DOCUMENT_STUDIO_P7_INTEGRATION_STATUS.md`.

### Vérité produit vérifiée

- `StudioTabs.tsx` expose uniquement P1→P6 ;
- `DocumentStudioVocabulary.ts` ne contient plus `plan` ;
- le type `CertifiableDocumentStudioTab` couvre uniquement les six pages documentaires actives ;
- le T2 navigateur actuel contient `assertCompanionAbsent(...)` et échoue si le Compagnon Diagnostique redevient visible ;
- commit `a294dacc...` : retrait explicite du tab diagnostique ;
- commit `8e8bb2c...` : contrat réduit aux tabs produisant des documents ;
- `TreatmentPlanStudio.tsx` existe encore, mais comme code dormant et avec des sorties cliniques/thérapeutiques spécifiques : sa présence ne prouve ni exposition produit ni validation scientifique.

### Statut des anciens lots

Les lots historiques P7-A/B/D/F/G conservent de la valeur comme durcissement de code dormant : warning-only sur signaux ATCD, reset patient, no-match legacy fail-closed, dirty-state, wording moins prescriptif, responsive/a11y.

Ils **ne doivent plus être interprétés comme la fermeture engineering d’une page active**, puisque cette page a ensuite été retirée du contrat certifiable.

Le harness `scripts/certify_document_studio_p7.sh` reste une régression de code historique ; il ne certifie pas un runtime P7 actif.

### Décision canonique

- ne pas réactiver silencieusement `plan` ;
- ne pas lancer de certification runtime P7 comme si la surface existait encore ;
- conserver le code dormant jusqu’à décision explicite de réactivation ou suppression ;
- toute réactivation future = **nouveau chantier produit + clinique** avec contexte structuré, provenance/version/evidence, validation scientifique humaine, runtime patient A→B et cycle UI BEFORE/mockup/AFTER ;
- pour le Document Studio actuel, **T1 est le prochain lot transversal exécutable après P6**.

---

## T1 — Audit transversal premium

**État : 🟡 T1-A→T1-E convergés en engineering sur PR #88/#89/#91/#92/#93 ; T1-F harness/closeout sur PR #94 ; runtime/CI/visuel non certifiés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_T1_TRANSVERSAL_PREMIUM_AUDIT.md`.

### Engineering acquis historique

- **T1-A patient isolation** : remount par patient, reset atomique du store comptable et de l’édition archivée, invalidation des dirty states, protections contre réponses patient/suggestion tardives ;
- **T1-B navigation** : policy dirty-state et transitions Document Studio centralisées ;
- **T1-C frontière clinique** : suppression du side-channel Ghost/free-text/financial labels ; sécurité ordonnance dédiée conservée ; exécuteur direct `ai-diagnostic` neutralisé dans le Studio certifiable ;
- **T1-D vérité UI** : surfaces Header/Tabs/Footer/Preview contrôlées et gate anti-régression contre les claims runtime/IA trompeurs ;
- **T1-E responsive/a11y** : labels/états accessibles, cibles tactiles, focus visible, dialogues impression/preview, Escape preview, iframe titrée, durcissement mobile ;
- **T1-F préparé** : `scripts/certify_document_studio_t1.sh` regroupe régression T1 ciblée, full frontend et build production.

### Limite de preuve

Le harness T1 est **préparé mais non exécuté** sur le `master` actuel. Les anciennes affirmations P1→P7 doivent être relues dans le contrat produit actuel P1→P6, P7 étant désormais explicitement dormant/hors Studio certifiable.

### Reste

- exécuter `scripts/certify_document_studio_t1.sh` sur le head final avec Node 20 ;
- recertifier la matrice active P1→P6 : isolation patient, dirty-state/navigation manuelle + URL, vérité UI, aucune route Studio vers `ai-diagnostic` ;
- navigateur réel 390/430/1280, clavier/focus, preview/impression ;
- seulement après ces preuves : certification T1, closeout, merge et transition T2.

---

## T2 — Refonte intelligente finale / recertification globale

**État : ⬜ après fermeture des gates exécutables T1 sur le périmètre actif P1→P6.**

À couvrir : cartographie finale, matrice garder/améliorer/fusionner/cacher/supprimer/refaire, navigation cible, hiérarchie, priorités, critères UX/fonctionnels, régression globale et recertification finale.

P7 dormant n’entre dans T2 que comme dette/code historique à classer : conserver hors produit, supprimer, ou rouvrir via un chantier produit/clinique séparé.

---

## Migration des anciens identifiants

| Ancien identifiant | Portée historique | Canonique |
|---|---|---|
| P1 / R1-R7 | Ordonnance | **P1** |
| P2-A, P2-C, P2-D | Devis / comptable partagé | **P3** principalement |
| P2-B, P2-E, P2-F | Honoraires / comptable partagé | **P4** principalement |
| P3 Certificat | Certificat | **P2** |
| P3-C→P3-H Document Libre | Document Libre | **P6** |
| P4-A/P4-B | Échéancier/paiements | **P5** |
| P5-P0 | Compagnon/safety historique | **P7 dormant / hors Studio certifiable** |
| ancien P6 | transversal | **T1** |
| ancien P7 | refonte finale | **T2** |

---

## Chemin critique courant

1. **P3 PR #77** : dette historique à réconcilier séparément avec le `master` moderne ; ne pas réintroduire une ancienne stack par simple merge.
2. **P4 Note Honoraires** : engineering/runtime automatisé fermé ; gates humaines externes séparées.
3. **P5 Suivi Paiement** : engineering/runtime/PDF/responsive automatisés certifiés ; contrepassation réelle reste séparée.
4. **P6 Document Libre** : **fermé et mergé** sur `master` `e5a9f37...` après CI/T2 exact-head verts.
5. **P7 Compagnon Diagnostique** : **retiré du Studio certifiable** ; code dormant, aucune réactivation implicite.
6. **T1** : **prochain lot exécutable** sur le périmètre actif P1→P6 ; lancer harness + runtime/browser puis closeout.
7. **T2** : recertification/refonte finale après T1 ; classer définitivement la dette P7 dormant.

## Infrastructure CI

P4 dispose de runs réels verts sur son HEAD produit certifié : T2 `34413159443` et CI `34413159336`.

P5 dispose de runs réels verts sur son HEAD comportemental `63d33c2c...` : T2 `34520821872` (#2167) et CI `34520821875` (#3156).

P6 dispose de runs réels verts sur son HEAD comportemental `218e7ef...` : T2 `34528255978` (#2191) et CI `34528255939` (#3183), puis sur le HEAD closeout `9269f9c...` : T2 `34582263341` (#2229) et CI `34582263330` (#3224). PR #405 squash-mergée sur `master` `e5a9f37...`.

Le harness T1 canonique est `scripts/certify_document_studio_t1.sh` et doit être exécuté sur le `master` moderne / branche de certification dédiée avant tout claim T1.

## Règle de progression

**audit → vérité produit actuelle → défauts classés → correctifs réversibles → tests ciblés → CI si disponible → runtime/visuel selon risque → audit/status canonique → roadmap → lot suivant.**
