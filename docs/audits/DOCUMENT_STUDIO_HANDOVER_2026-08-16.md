# Document Studio — handover — 2026-08-16

## Objectif

Poursuivre le chantier depuis **T2 — Refonte intelligente finale / recertification globale**, sans rouvrir P1→T1 sauf régression démontrée.

## État vérifié

- P1 Ordonnance : engineering fermé + recertification visuelle ; gates clinique/runtime séparés.
- P2 Certificat : engineering convergé ; runtime/PDF final différé.
- P3 Devis : **CLOSED / PAUSED** jusqu'à nouvel ordre ; PR #77 draft.
- P4 Note Honoraires : engineering local convergé ; PR #90 draft.
- P5 Suivi Paiement : engineering local convergé ; PR #95 draft.
- P6 Document Libre : engineering local convergé ; PR #96 draft.
- P7 Compagnon Diagnostique : engineering safety local convergé ; PR #97 draft.
- T1 Audit transversal premium : engineering transversal local convergé ; PR #101 draft.
- **T2 : prochaine tâche active.**

## Dernières preuves principales

### P5
- backend : 15/15 PASS ;
- summary : 4/4 PASS ;
- create payload : `tsc --strict` + 8/8 PASS.

### P6
- dirty/archive : `tsc --strict` + 11/11 PASS.

### P7
- safety : `tsc --strict` + 8/8 PASS ;
- P7→P3 + dirty : `tsc --strict` + 12/12 PASS.

### T1
- navigation partagée : `tsc --strict` + 10/10 PASS ;
- legacy échéancier `/documents/generate` désactivé : helper 4/4 PASS ;
- Certificat dirty-state rétabli ;
- query-param ne contourne plus les gardes ;
- archive-success explicite : preview/erreur/409 ne nettoient plus les brouillons ;
- P5 stale-print supprimé et impression déclarée non persistante ;
- ghost `ai` Document Studio et appel `/ai-diagnostic` retirés du hook ;
- Header partagé nettoyé.

## Branches / PR

- P3 : `agent/p3d-devis-phases-learning` — PR #77 draft.
- P4 : `agent/p4-note-honoraires-audit` — PR #90 draft.
- P5 : `agent/p5-suivi-paiement-audit` — PR #95 draft.
- P6 : `agent/p6-document-libre-recertification` — PR #96 draft.
- P7 : `agent/p7-compagnon-diagnostique-audit` — PR #97 draft.
- T1 : `agent/t1-document-studio-transversal-audit` — PR #101 draft.

## Canonique

`DOCUMENT_STUDIO_ROADMAP.md` est la source de vérité actuelle.
Aucune pondération officielle : **pourcentage global indéterminé**.

## Prochaine action exacte — T2

1. supprimer/neutraliser les restes legacy devenus inatteignables ;
2. réduire listeners/props/callbacks partagés redondants sans retirer les gardes ;
3. compléter l’accessibilité des modales partagées ;
4. créer un harness de certification Document Studio unique et fail-closed ;
5. vérifier cohérence des PR stackées et audits ;
6. exécuter tous les tests locaux réellement disponibles ;
7. documenter les gates full-app/runtime/PDF/browser externes ;
8. ne pas merger/ready tant que les gates requis ne sont pas réellement fermés.

## Anomalies T1 consignées pour T2

- `DocumentFactory.create_installment_plan()` est devenu inatteignable par le `DocumentRequest` public et paraît legacy ;
- certains listeners `beforeunload` locaux restent redondants avec le Hub ;
- quelques props historiques du footer sont inutilisées ;
- la modale doublon du Hub mérite la même sémantique ARIA explicite que la modale navigation ;
- full build/tests/browser restent indisponibles dans l’environnement courant.
