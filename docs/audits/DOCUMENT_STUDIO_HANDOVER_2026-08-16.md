# Document Studio — handover — 2026-08-16

## Objectif

Poursuivre l'audit/correction page par page du Document Studio sans rouvrir les pages déjà convergées sauf régression démontrée.

## État vérifié

- **P1 Ordonnance** : engineering fermé + recertification visuelle ; gates clinique/runtime séparés.
- **P2 Certificat** : engineering convergé ; runtime/PDF final différé.
- **P3 Devis** : **CLOSED / PAUSED jusqu'à nouvel ordre** ; PR #77 open + draft ; full-app non revendiqué.
- **P4 Note Honoraires** : engineering local convergé ; PR #90 draft.
- **P5 Suivi Paiement** : engineering local convergé ; PR #95 draft ; audit `DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md`.
- **P6 Document Libre** : engineering local convergé ; PR #96 draft ; audit `DOCUMENT_STUDIO_P6_DOCUMENT_LIBRE_AUDIT.md`.
- **P7 Compagnon Diagnostique** : **prochaine page active**.

## Dernières preuves

### P5
- backend création/update/suppression : 15/15 PASS ;
- summary tracking : 4/4 PASS ;
- create payload : `tsc --strict` + 8/8 PASS.

### P6
- dirty/archive policy : `tsc --strict` PASS + 11/11 assertions PASS ;
- correction : dirty-state nettoyé uniquement après vrai succès d'archive Libre avec `pdf_url` ; preview/échec/409/autre type conservent l'état sale.

## Branches / PR

- P3 : `agent/p3d-devis-phases-learning` — PR #77 draft.
- P4 : `agent/p4-note-honoraires-audit` — PR #90 draft.
- P5 : `agent/p5-suivi-paiement-audit` — PR #95 draft.
- P6 : `agent/p6-document-libre-recertification` — PR #96 draft, base P5.

## Canonique

`DOCUMENT_STUDIO_ROADMAP.md` est la source de vérité page-par-page actuelle.
Aucune pondération officielle n'existe : ne pas inventer de pourcentage global.

## Prochaine action exacte

Créer P7 depuis le head P6 courant, puis auditer dans cet ordre :
1. arbre réel des états/questions ;
2. contexte patient réellement consommé ;
3. nature des sorties et niveau de certitude ;
4. validation praticien avant action clinique ;
5. P7→P3 Devis et filtres ;
6. P7→P1 Ordonnance/autres documents ;
7. conservation/perte d'état inter-pages ;
8. callbacks/branches orphelins ;
9. UX/accessibilité/responsive ;
10. validation scientifique humaine séparée de l'engineering.

## Gates différés communs

Les PR P3→P6 restent draft tant que les gates full-app applicables ne sont pas exécutés : build/tests complets, runtime authentifié, PDF cabinet, browser/responsive, merge/post-merge.