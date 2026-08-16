# Document Studio — handover — 2026-08-16

## Objectif

Poursuivre le chantier Document Studio depuis **T1 — Audit transversal premium**, sans rouvrir P1→P7 sauf régression transversale démontrée.

## État vérifié

- **P1 Ordonnance** : engineering fermé + recertification visuelle ; gates clinique/runtime séparés.
- **P2 Certificat** : engineering convergé ; runtime/PDF final différé.
- **P3 Devis** : CLOSED / PAUSED jusqu'à nouvel ordre ; PR #77 draft.
- **P4 Note Honoraires** : engineering local convergé ; PR #90 draft.
- **P5 Suivi Paiement** : engineering local convergé ; PR #95 draft.
- **P6 Document Libre** : engineering local convergé ; PR #96 draft.
- **P7 Compagnon Diagnostique** : engineering safety local convergé ; PR #97 draft.
- **T1 Audit transversal premium** : prochaine tâche active.

## Dernières preuves

### P5
- backend création/update/suppression : **15/15 PASS** ;
- summary tracking : **4/4 PASS** ;
- create payload : `tsc --strict` + **8/8 PASS**.

### P6
- dirty/archive policy : `tsc --strict` + **11/11 PASS**.

### P7
- anciennes sorties `Diagnostic Établi`, substitutions thérapeutiques automatiques et plans médicaux hardcodés supprimés ;
- contexte patient lecture seule ;
- actes saisis manuellement + confirmation explicite du praticien uniquement ;
- P7→P3 : prix 0, aucune dent inventée, instructions médicamenteuses filtrées ;
- dirty-state protégé sur onglet + fermeture navigateur ;
- policy safety : `tsc --strict` + **8/8 PASS** ;
- chaîne P7→P3 + dirty : `tsc --strict` + **12/12 PASS**.

## Branches / PR

- P3 : `agent/p3d-devis-phases-learning` — PR #77 draft.
- P4 : `agent/p4-note-honoraires-audit` — PR #90 draft.
- P5 : `agent/p5-suivi-paiement-audit` — PR #95 draft.
- P6 : `agent/p6-document-libre-recertification` — PR #96 draft.
- P7 : `agent/p7-compagnon-diagnostique-audit` — PR #97 draft.

## Canonique

`DOCUMENT_STUDIO_ROADMAP.md` est la source de vérité page-par-page actuelle.
Aucune pondération officielle : **pourcentage global indéterminé**.

## Prochaine action exacte — T1

Créer T1 depuis le head P7 courant et auditer d'abord :
1. bypass des dirty-state par navigation/query params ;
2. lifecycle partagé preview/archive/print/duplicate ;
3. fragmentation des dirty-state ;
4. permissions/contrats backend communs ;
5. responsive/accessibilité des composants partagés ;
6. callbacks/branches mortes et duplication ;
7. nomenclature/messages transactionnels ;
8. transitions inter-pages.

Signal prioritaire à vérifier : `DocumentHub` applique directement `setActiveTab(nextTab)` lors d'un changement `documentTab` dans l'URL, ce qui peut contourner les gardes `StudioTabs`.

## Gates différés communs

P3→P7 restent draft tant que les gates full-app applicables ne sont pas exécutés : build/tests complets, runtime authentifié, PDF cabinet, browser/responsive, merge/post-merge.