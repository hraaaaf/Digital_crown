# Document Studio — T2 certification handover — 2026-08-16

## Objectif

Reprendre uniquement la **certification finale** du Document Studio. Aucun correctif critique engineering connu ne reste ouvert dans le périmètre audité P1→P7/T1/T2.

## État

- P1 Ordonnance : engineering fermé ; validation clinique/runtime séparée.
- P2 Certificat : engineering convergé ; runtime/PDF différé.
- P3 Devis : CLOSED / PAUSED sur décision produit ; PR #77 draft.
- P4 Note Honoraires : engineering local convergé ; PR #90 draft.
- P5 Suivi Paiement : engineering local convergé ; PR #95 draft.
- P6 Document Libre : engineering local convergé ; PR #96 draft.
- P7 Compagnon Diagnostique : engineering safety local convergé ; PR #97 draft.
- T1 Transversal : engineering local convergé ; PR #101 draft.
- T2 : engineering closeout local convergé ; PR T2 draft sur branche `agent/t2-document-studio-final-recertification`.

## Derniers changements T2

- Libre : suppression du `beforeunload` et de l'interceptor archive locaux ; Hub = autorité lifecycle.
- `scripts/certify_document_studio.sh` créé comme harness fail-closed final.
- `DocumentNavigationPolicy.test.ts` versionné.
- `DiagnosticCompanionPolicy.test.ts` versionné.
- audit final : `docs/audits/DOCUMENT_STUDIO_T2_FINAL_RECERTIFICATION.md`.

## Preuves déjà acquises

- P3 backend 26/26 ; frontend ciblé 39/39 ; PDF long lisible.
- P4 backend 13/13 ; héritage échéancier 4/4 ; hydration 1/1 ; PDF long 36/36 lignes / 6 pages.
- P5 backend 15/15 ; summary 4/4 ; create payload 8/8 + tsc.
- P6 dirty/archive 11/11 + tsc.
- P7 safety 8/8 + tsc ; P7→P3 + dirty 12/12 + tsc.
- T1 navigation 10/10 + tsc ; legacy installment path 4/4.
- T2 harness : `bash -n` PASS.

Ces preuves sont locales/ciblées et ne valent pas full-project certification.

## Prochaine action exacte

Sur un checkout propre du **head candidat T2 exact**, avec Python 3.12 / Node 20 et toutes les dépendances :

```bash
bash scripts/certify_document_studio.sh
```

Ne considérer le gate automatisé fermé que si le script imprime réellement :

```text
AUTOMATED_DOCUMENT_STUDIO_GATES_PASS
```

## Puis exécuter, dans cet ordre

1. runtime authentifié P1→P7 ;
2. navigation clic + `documentTab` avec brouillons ;
3. preview/archive/reopen/duplicate cancel+force ;
4. impression fraîche, notamment P5 ;
5. P5 création/reload/paiement réel ;
6. P7→P3 confirmé ;
7. PDF cabinet court/long/A4/A5/branding/signature ;
8. browser 390 / 768 / desktop + clavier/touch/focus ;
9. validations humaines clinique/scientifique/réglementaire/financière applicables ;
10. seulement alors : ready review, merge ordonné, canoniques master, post-merge recertification.

## Interdictions

- ne pas merger les PR stackées avant gates applicables ;
- ne pas déduire production-ready de tests locaux ;
- ne pas rouvrir P3 tant que la décision produit de pause n'est pas explicitement levée ;
- ne pas réintroduire de chemin IA/LLM dans Document Studio sans décision d'architecture et validation dédiée.

## Blocage actuel

L'environnement de cette session ne fournit pas le checkout full-repository exact avec toolchain Python 3.12 / Node 20 et runtime cabinet authentifié. Le verrou restant est donc **exécution/certification externe**, pas un correctif de code connu.