# Document Studio — roadmap canonique page par page

## Objectif

Auditer, corriger et recertifier le Studio documentaire de Digital Crown **page par page, dans l’ordre visuel réel de l’interface**, sans confondre code vérifié, tests exécutés, runtime observé et certification métier.

Ordre canonique :

1. **P1 — Ordonnance**
2. **P2 — Certificat**
3. **P3 — Devis**
4. **P4 — Note Honoraires**
5. **P5 — Suivi Paiement**
6. **P6 — Document Libre**
7. **P7 — Compagnon Diagnostique**
8. **T1 — Audit transversal premium**
9. **T2 — Refonte intelligente finale / recertification globale**

Les anciens identifiants techniques sont conservés dans les PR/commits/audits historiques ; ils ne redéfinissent pas le numéro de page.

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

Preuves principales : PR #17/#19/#20/#21/#22/#23/#26 ; closeout visuel PR #43, recapture et post-merge historiques documentés dans l’audit.

Reste : interaction authentifiée locale et certification clinique/pharmacologique humaine.

---

## P2 — Certificat

**État : ✅ engineering convergé ; ⏳ certification finale runtime/PDF non fermée.**

Rapport historique : `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md`.

Acquis : nature explicite, dates/durée séparées, aucun choix clinique prérempli, texte libre praticien, contrat backend, signature manuscrite dentiste, impression fraîche, intégrité PDF, QR neutralisé sans contrat valide.

Reste : régression master finale, runtime authentifié, inspection PDF et certification réglementaire/clinique si requise.

---

## P3 — Devis

**État : 🟡 P3-A→P3-G intégrés sur PR #77 ; P3-H partiellement exécuté ; PR toujours draft/non mergée.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_INTEGRATION_STATUS.md` sur la branche P3.

Acquis sur #77 : isolation financière P3/P5, source de vérité odontogramme, catalogue/dentition, phases non financières, apprentissage autoritatif, conversion Plan→Devis, suppression suggestion RDV financière générique, PDF lisible multipage, responsive/accessibilité engineering.

Preuves P3-H déjà exécutées dans le harness P3 : backend ciblé 13 passed ; policies frontend 22 groupes ; odontogramme 9 groupes ; PriceBrain 1 groupe ; PDF long 36 actes → 3 pages, en-tête répété, minimum observé 7,5 pt. Ces preuves ne remplacent pas un run full-repo/runtime.

Reste : suite complète + build, smoke authentifié, PDF cabinet réel, inspection responsive réelle, merge et post-merge.

---

## P4 — Note Honoraires

**État : 🟡 audit canonique effectué ; P4-A/P4-B financièrement durcis sur PR #79 ; CI/runtime non certifiés.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P4_HONORAIRES_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_IMPLEMENTATION_STATUS.md`.

### Engineering acquis sur #79

- statut documentaire fermé ; `PARTIEL` reste refusé sans montant encaissé explicite ;
- note/acte vide refusés ;
- montant fini, strictement positif, ≤ 1 000 000 MAD par ligne ;
- double frontière request + pré-PDF + persistance comptable ;
- pour `PAYE`, mode de règlement explicite obligatoire, sans fallback silencieux ;
- pour `EN_ATTENTE`, aucun mode n’est exigé puisqu’aucun encaissement n’est créé ;
- allocation exacte `Acte ↔ Payment` historique conservée ;
- réconciliation exacte d’une note globale avec échéances conservée ;
- tests ciblés ajoutés aux niveaux request, pré-PDF et persistance.

### Reste

- réconciliation P3→P4 avec #77 avant merge, afin de ne pas dupliquer/conflicter le lifecycle partagé ;
- traiter la suggestion radio par mots-clés dans ce même closeout partagé ;
- suite complète/build ;
- runtime authentifié ;
- preview/archive/impression/PDF ;
- responsive/accessibilité ;
- certification financière séparée.

---

## P5 — Suivi Paiement

**État : 🟡 audit canonique effectué ; contrat serveur + lifecycle explicite implémentés sur PR #79 ; CI/runtime non certifiés.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_IMPLEMENTATION_STATUS.md`.

### Engineering acquis sur #79

- création/preview : titre, total, lignes, montants et statuts fail-closed ;
- réconciliation exacte au centime côté serveur ;
- chemin documentaire direct `echeancier` durci avec dates explicites ;
- endpoint `latest` explicite et ordre serveur déterministe ;
- échéance PAYE non réouvrable/non rechiffrable sans contrepassation ;
- suppression d’un plan déjà encaissé refusée ;
- UI : `brouillon équilibré → enregistrer → encaisser` ;
- ancien checkbox local « Réglé » supprimé ;
- aucun mode de paiement présélectionné ; encaissement désactivé jusqu’au choix explicite ;
- montants persistés figés ; restructuration via nouveau plan ;
- résumé total/payé/restant ;
- WhatsApp manuel uniquement ;
- tableau scrollable horizontalement sur petit écran ;
- tests schema, route et frontend ajoutés/alignés.

### Reste

- supprimer/réconcilier le chargement P5 historique dans le store comptable global après intégration P3 #77 ; P5 n’en dépend plus fonctionnellement ;
- suite complète/build ;
- runtime authentifié création/sauvegarde/encaissement/contrepassation ;
- PDF et responsive réel 1440/768/390 ;
- certification financière séparée.

---

## P6 — Document Libre

**État : ✅ engineering convergé ; ⏳ certification finale runtime/PDF non fermée.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P6_DOCUMENT_LIBRE_AUDIT.md` ;
- historique partagé `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md` ;
- statut : `docs/audits/DOCUMENT_STUDIO_P4_P6_IMPLEMENTATION_STATUS.md`.

Acquis : validation titre/contenu, toolbar non-submit, contrat/PDF sûr, allowlist markup, PDF long/multipage, impression fraîche, auto-preview invalide silencieux, dirty-state, permission clinique, archive/réouverture.

Aucun nouveau P0 statique démontré dans le chantier P4-P6 ; aucune réarchitecture artificielle ajoutée.

Reste : régression frontend/backend/PDF réelle, runtime authentifié, inspection A4/A5/multipage/tableaux/caractères spéciaux, responsive/accessibilité. WYSIWYG/templates = amélioration produit, pas gate sécurité.

---

## P7 — Compagnon Diagnostique

**État : 🟡 frontière safety partiellement fermée ; audit complet restant.**

Acquis historique : ancien P5-P0 / PR #38, pharmacovigilance/substitution fail-closed.

Reste : arbre d’états, contexte patient, sorties diagnostiques, validation praticien, connexions P7→P3/P1, état inter-pages, callbacks, valeur clinique, validation scientifique humaine.

---

## T1 — Audit transversal premium

**État : ⬜ après convergence des pages ou lorsqu’un défaut transversal bloque plusieurs pages.**

À couvrir : navigation, header/footer/actions, dirty-state, preview, responsive, typographie/contraste, dark mode, clavier, terminologie, loading/empty/error/success, accessibilité, cohérence clinique/financière/documentaire.

---

## T2 — Refonte intelligente finale / recertification globale

**État : ⬜ après P1→P7 + T1.**

À couvrir : cartographie finale, matrice garder/améliorer/fusionner/cacher/supprimer/refaire, navigation cible, hiérarchie, priorités, critères UX/fonctionnels, régression globale et recertification finale.

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
| P5-P0 | Compagnon/safety | **P7** |
| ancien P6 | transversal | **T1** |
| ancien P7 | refonte finale | **T2** |

Les PR, commits et audits historiques ne sont pas renommés rétroactivement.

---

## Chemin critique courant

1. **P3 #77** : fermer ses gates full-repo/runtime et merger lorsqu’ils passent.
2. **P4/P5 #79** : réconcilier les dépendances partagées avec P3, puis exécuter suite complète/build/runtime/PDF et certification financière.
3. **P6** : exécuter la recertification finale runtime/PDF sur le master convergé.
4. **P7**, puis **T1**, puis **T2**.

## Infrastructure CI

Sur les heads P3/P4/P5 récents observés, GitHub Actions a échoué avant exécution des steps (`steps=null`). Ce blocage runner/billing est consigné comme externe. Il ne justifie ni PASS ni échec applicatif et ne bloque pas le travail indépendant.

## Règle de progression

**audit → défauts classés → correctifs réversibles → tests ciblés → CI si disponible → runtime/visuel selon risque → audit/status canonique → roadmap → page suivante.**
