# Document Studio — roadmap canonique page par page

## Objectif

Auditer, corriger et recertifier le Studio documentaire de Digital Crown **page par page**, sans confondre code vérifié, tests exécutés, runtime observé et certification métier.

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

**État : 🟡 audit canonique + durcissement engineering intégrés après P3 sur `agent/p4-p6-after-p3` ; certification runtime/financière ouverte.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P4_HONORAIRES_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md`.

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
- tests request, pré-PDF, persistance, absence d’inférence clinique et store ajoutés.

### Reste

- exécution réelle du harness/full-suite/build sur le stack P3→P6 ;
- runtime authentifié EN_ATTENTE/PAYE, archive/doublon/impression ;
- rapprochement `Acte ↔ Payment` dans le dossier patient ;
- PDF réel et responsive/accessibilité ;
- certification financière séparée.

---

## P5 — Suivi Paiement

**État : 🟡 audit canonique + contrat/lifecycle intégrés après P3 ; certification runtime/financière ouverte.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md`.

### Engineering acquis

- création/preview/mutation fail-closed : titre, total, lignes, dates, montants, statuts ;
- réconciliation exacte au centime ;
- endpoint `latest` explicite et tri déterministe ;
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
- tests schema, route et frontend ajoutés/alignés.

### Reste

- exécution réelle full-suite/build ;
- runtime authentifié création/sauvegarde/encaissement ;
- rapprochement `Payment ↔ installment` ;
- scénario de contrepassation à définir/certifier séparément ;
- PDF et responsive réel 1440/768/390 ;
- certification financière finale.

---

## P6 — Document Libre

**État : ✅ engineering convergé + matrice de certification automatisée préparée ; ⏳ exécution/runtime/PDF visuel non fermés.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P6_DOCUMENT_LIBRE_AUDIT.md` ;
- historique `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md` ;
- statut stack : `docs/audits/DOCUMENT_STUDIO_P4_P6_AFTER_P3_STATUS.md`.

Acquis : validation titre/contenu, toolbar non-submit, contrat/PDF sûr, allowlist markup, document long/multipage, impression fraîche, auto-preview invalide silencieux, dirty-state, permission clinique, archive/réouverture.

Couverture automatisée existante/ajoutée : sécurité markup, permissions, caractères spéciaux, multipage lisible, A4/A5 sur dimensions PDF, destinataire/date personnalisés et tableau Markdown.

Harness stack : `scripts/certify_document_studio_p3_p6.sh` regroupe régression ciblée P3→P6, full backend, frontend ciblé/full, build et prod-safety fail-closed.

Aucun nouveau P0 statique démontré dans le chantier actuel.

Reste : exécuter réellement le harness sur le head final, runtime authentifié, inspection A4/A5/multipage/tableaux/caractères spéciaux, responsive/accessibilité. WYSIWYG/templates = amélioration produit, pas gate sécurité.

---

## P7 — Compagnon Diagnostique

**État : 🟡 P7-A/B/D/F/G fermés en engineering ; P7-C/E/H ouverts ; aucune certification d’exécution/scientifique revendiquée.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P7_COMPAGNON_DIAGNOSTIQUE_AUDIT.md` ;
- `docs/audits/DOCUMENT_STUDIO_P7_INTEGRATION_STATUS.md`.

### Architecture vérifiée

- onglet actif : `plan` ;
- composant actif : `TreatmentPlanStudio` ;
- contexte patient lu via `/patients/{patientId}` ;
- sortie éditable puis conversion explicite P7→P3 ;
- conversion Devis financièrement neutre (`price = 0`) ;
- moteurs legacy parallèles : `HouseWizard` / `DiagnosticEngine` / `SafeDiagnosticEngine`.

### Engineering acquis

- **P7-A** : aucune substitution thérapeutique automatique à partir des ATCD texte libre ; warning-only pénicilline/AINS ; changement patient atomique avec protection contre réponse réseau stale ;
- **P7-B** : no-match legacy fail-closed, sans diagnostic rassurant, médicament ni traitement par défaut ;
- **P7-D** : résultat présenté comme hypothèse/proposition à confirmer ; claims scientifiques non sourcés retirés du parcours actif ;
- **P7-F** : dirty-state, garde changement d’onglet, `beforeunload`, nettoyage après reset/conversion ;
- **P7-G** : engineering mobile/tactile/clavier/accessibilité ;
- P7→P3 reste neutre : prix zéro, aucune dent inventée si absente, propositions vides supprimées.

### Couverture préparée

`scripts/certify_document_studio_p7.sh` regroupe les tests réellement présents P7-A/B/D/F/G, le contrat P7→P3, la full-suite frontend et le build.

**Le harness est écrit mais aucun PASS n’est revendiqué tant qu’il n’a pas réellement tourné sur le head final.**

### Ouvert

- **P7-C — contexte clinique structuré** : le schéma patient inspecté ne démontre qu’un `antecedents_medicaux` texte libre, sans source allergies structurée ; nécessite évolution du modèle patient et gouvernance clinique ;
- **P7-E — provenance/version/evidence** : aucun modèle canonique persistant de proposition/rule-set/version/entrées/warnings/confirmation praticien n’est défini ; nécessite décision d’architecture ;
- **P7-H — validation scientifique + recertification** : revue médicale humaine, sources/versionnement, cas positifs/négatifs/no-match, runtime authentifié patient A→B, 390/768/desktop et full-regression.

Les deux P0 statiques du baseline sont corrigés en engineering ; la page **n’est pas certifiée** tant que les gates d’exécution et C/E/H restent ouverts.

---

## T1 — Audit transversal premium

**État : ⬜ prochain chantier exécutable après closeout engineering P7.**

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

---

## Chemin critique courant

1. **P3 PR #77** : fermer full-repo/runtime/visuel/merge dès qu’une exécution réelle redevient possible.
2. **Stack P4/P5/P6 PR #80** : engineering/documentation fermé sur son head ; CI/runtime/PDF/financier externes ouverts.
3. **P7 stack #81→#86** : A/B/D/F/G engineering fermé ; exécuter le harness/runtime quand l’infrastructure le permet ; P7-C/E nécessitent architecture dédiée ; P7-H est un gate scientifique humain.
4. **T1** : lancer l’audit transversal premium maintenant, car c’est le prochain travail indépendant immédiatement exécutable.
5. **T2** après T1 et après consolidation des gates restants.

## Infrastructure CI

Sur les heads récents P3/P4/P5/P7, GitHub Actions a pu soit échouer avant exécution des steps (`steps=null`), soit ne créer aucun run observable. Ces conditions externes ne justifient ni PASS ni échec applicatif et ne bloquent pas le travail indépendant.

Sur le head final P4→P6 `fb75780c44d21e552b396d1f4376b657e8837994`, aucun workflow run ni status context réel n'était observable au contrôle effectué. Les heads P7-A/B/D/F/G contrôlés n’ont pas non plus produit de run observable au moment du contrôle. Aucun PASS n'est revendiqué.

## Règle de progression

**audit → défauts classés → correctifs réversibles → tests ciblés → CI si disponible → runtime/visuel selon risque → audit/status canonique → roadmap → page suivante.**
