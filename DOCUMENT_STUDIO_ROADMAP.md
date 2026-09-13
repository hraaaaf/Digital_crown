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

**État : ✅ engineering fermé + recertification visuelle réalisée ; gates cliniques humaines séparées.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md`.

Acquis : safety fail-closed, dirty-state, habitudes/protocoles, contexte patient, preview responsive, visuel multi-viewport. La matrice T2 actuelle couvre aussi la page dans la surface P1→P6.

---

## P2 — Certificat

**État : ✅ engineering convergé ; runtime transversal actuel couvert par T2.**

Rapport historique : `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md`.

Acquis : nature explicite, dates/durée séparées, aucun choix clinique prérempli, texte libre praticien, contrat backend, signature, impression fraîche, intégrité PDF. Les validations réglementaires/cliniciennes humaines restent indépendantes.

---

## P3 — Devis

**État : 🟡 dette historique documentée ; comportement actuel inclus dans la recertification T2.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_INTEGRATION_STATUS.md`.

Les anciennes PR P3 ne doivent pas être remergées mécaniquement dans le `master` moderne. Le runtime actuel T2 certifie notamment l’absence de mutation financière parasite lors de la génération du Devis.

---

## P4 — Note Honoraires

**État : ✅ engineering + runtime automatisé fermés ; validations comptable/réglementaire humaines séparées.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P4_HONORAIRES_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_FINAL_CERTIFICATION_2026-09-09.md`.

HEAD produit historiquement certifié : `99c63b1247448805360e949d6da745afa53ba340`.

Le T2 courant repasse les invariants P4 : invalides 422 sans mutation, EN_ATTENTE sans Payment, PAYE avec Payment exact, réhydratation du statut et réconciliation persistée.

---

## P5 — Suivi Paiement

**État : ✅ engineering + runtime/PDF/responsive automatisés certifiés ; contrepassation comptable réelle séparée.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md`.

HEAD comportemental historique : `63d33c2c926120fec45174aba831c1154e48b35a`.

Le T2 courant repasse la réconciliation du plan de paiement, dont total `1200.0`, lignes `500.0 + 700.0` et encaissé `500.0`.

---

## P6 — Document Libre

**État : ✅ engineering + CI + runtime/PDF/responsive certifiés, PR #405 mergée et `master` vérifié.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P6_DOCUMENT_LIBRE_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md`.

HEAD comportemental certifié : `218e7ef1580e69958f02d9e8319750772f273376`.
HEAD closeout exact : `9269f9c4111b1c7ce58dfcaa748b4b56cf892b13`.
Merge squash historique : `e5a9f37fe33690759124cadb18d672d756647578`.

Le T2 actuel repasse P6 aux viewports 390×844, 768×1024 et 1280×900 sans overflow ni clipping, ainsi que PDF, print et fraîcheur.

---

## P7 — Compagnon Diagnostique

**État : ⛔ surface retirée du Document Studio certifiable ; code historique dormant ; aucune certification runtime/scientifique active revendiquée.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P7_CURRENT_PRODUCT_TRUTH_2026-09-11.md` ;
- historique `docs/audits/DOCUMENT_STUDIO_P7_COMPAGNON_DIAGNOSTIQUE_AUDIT.md` ;
- historique `docs/audits/DOCUMENT_STUDIO_P7_INTEGRATION_STATUS.md`.

Vérité actuelle vérifiée :

- `StudioTabs.tsx` expose uniquement P1→P6 ;
- `DocumentStudioVocabulary.ts` ne contient plus `plan` ;
- le T2 échoue si le Compagnon Diagnostique redevient visible ;
- `TreatmentPlanStudio.tsx` reste du code dormant, pas une surface produit certifiée ;
- toute réactivation future = nouveau chantier produit + clinique avec validation scientifique humaine.

---

## T1 — Audit transversal premium

**État : 🟢 runtime transversal P1→P6 certifié sur HEAD comportemental ; closeout documentaire et exact-head final en cours.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_T1_TRANSVERSAL_PREMIUM_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_T1_CURRENT_SURFACE_2026-09-11.md`.

PR : #465 `test(t1): certify active P1-P6 transversal boundaries`.

HEAD comportemental certifié avant closeout documentaire : `51e98dd3f14882278e7de5a2f862bb7a256d985b`.

### Engineering acquis

- isolation patient et reset du state patient-scoped ;
- protection contre réponses patient tardives ;
- dirty-state/navigation centralisés ;
- frontières cliniques partagées durcies ;
- aucune entrée Document Studio active vers `ai-diagnostic` ;
- vérité UI/a11y/responsive durcie ;
- harness T1 réaligné sur **P1→P6** et P7 dormant exclu du gate ciblé ;
- credential T2 jetable généré à l'exécution ;
- limite de login élevée uniquement dans le serveur T2 isolé pour permettre les multiples probes du même run, sans changer la politique produit.

### Certification observée

T2 Runtime Browser Certification `#2645` / run `34750958888` : **SUCCESS**.
Job `T2 Browser Runtime Matrix` / `103707302825` : **SUCCESS**.

Le probe transversal T1 a observé :

- patient B autoritaire avant et après libération des réponses retardées de A ;
- aucune route error ;
- annulation URL dirty restaure l'URL et conserve le brouillon ;
- confirmation dirty atteint la cible ;
- Compagnon Diagnostique absent ;
- aucune requête `ai-diagnostic` ;
- aucune page error ;
- statut global : **PASS**.

La même exécution T2 a également passé :

- PDF runtime strict ;
- réconciliation P3/P4/P5 ;
- matrice navigateur active P1→P6 avec `greenPages=6/6` ;
- stress de navigation `10/10` transitions avec dirty guard observé ;
- P6 responsive 390/768/1280 ;
- impression navigateur ;
- fraîcheur PDF.

Artefact : `t2-browser-evidence`, ID `10316225660`, digest `sha256:886455c2ffcb560e50cb22e0e3798cc362459615904afec3da9c6396c2aaf333`.

Gates voisins sur le même HEAD comportemental :

- Catalog Connected Truth `#1094` / run `34750958896` : **SUCCESS** ;
- Cabinet Upgrade PostgreSQL `#160` / run `34750958994` : **SUCCESS** ;
- Patient P7 Final `#1309` / run `34750959000` : **SUCCESS** sans réactivation P7 dans le Studio ;
- M6-I `#1445` : **SKIPPED** attendu.

CI principal `#3701` / run `34750958892` n'était pas encore terminal lors du closeout intermédiaire. Les jobs frontend/tests/build et bridges M4 déjà terminés étaient verts ; le job backend principal restait en cours.

### Reste avant fermeture T1

1. obtenir la CI principale terminale verte ;
2. exécuter les gates sur le **HEAD documentaire final** ;
3. inspecter les preuves exact-head ;
4. squash merge PR #465 avec contrôle du HEAD attendu ;
5. vérifier `master` post-merge.

---

## T2 — Refonte intelligente finale / recertification globale

**État : ⬜ après fermeture formelle T1.**

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

1. **P1→P6** : surface active actuelle.
2. **P7** : retiré du Studio certifiable, aucune réactivation implicite.
3. **T1** : runtime P1→P6 prouvé vert sur le HEAD comportemental ; closeout/exact-head final/merge restent à fermer.
4. **T2** : lot suivant après fermeture formelle T1.

## Infrastructure CI

P4 : T2 `34413159443` et CI `34413159336` historiquement verts.

P5 : T2 `34520821872` (#2167) et CI `34520821875` (#3156) historiquement verts.

P6 : HEAD comportemental T2 `34528255978` (#2191) + CI `34528255939` (#3183), puis HEAD closeout T2 `34582263341` (#2229) + CI `34582263330` (#3224), tous verts ; PR #405 squash-mergée.

T1 : HEAD comportemental `51e98dd3...` avec T2 `34750958888` (#2645) **SUCCESS**, Catalog `34750958896` (#1094) **SUCCESS**, PostgreSQL `34750958994` (#160) **SUCCESS**, Patient P7 `34750959000` (#1309) **SUCCESS** ; CI `34750958892` (#3701) encore non terminale lors du closeout intermédiaire.

Le harness T1 canonique est `scripts/certify_document_studio_t1.sh`.

## Règle de progression

**audit → vérité produit actuelle → défauts classés → correctifs réversibles → tests ciblés → CI/runtime → audit/status canonique → roadmap → exact-head final → merge → post-merge → lot suivant.**
