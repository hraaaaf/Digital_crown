# Document Studio — T2 Refonte intelligente finale / recertification globale

Date : 2026-08-16
Branche : `agent/t2-document-studio-final-recertification`
Base : T1 Audit transversal premium

## Verdict

**Engineering local Document Studio convergé sur P1→P7 + T1/T2. Certification full-app / production NON revendiquée.**

Le closeout final automatique reste conditionné au harness full-repository et aux gates runtime/PDF/browser/humaines listées ci-dessous.

## T2-A — simplification des autorités de lifecycle

### Document Libre

Le formulaire Libre possédait encore :
- son propre `beforeunload` ;
- un interceptor Axios chargé de déduire qu'une archive Libre avait réussi.

Depuis T1, ces responsabilités appartiennent au `DocumentHub` et à `ArchiveSuccessSignal`.

Correction T2 :
- suppression du listener `beforeunload` local Libre ;
- suppression de l'interceptor Axios local ;
- conservation du registre `LibreDirtyState` comme état métier ;
- ouverture/réouverture établit une baseline propre ;
- navigation, abandon, beforeunload et archive-success restent centralisés au Hub.

Cela réduit le risque de doubles autorités et de nettoyages contradictoires.

## T2-B — harness final fail-closed

Nouveau script :

`scripts/certify_document_studio.sh`

Le harness :
1. réutilise `scripts/certify_p3_devis.sh`, qui porte déjà les contrôles exacts de toolchain/worktree, les tests P3, la suite backend complète, `npm test`, `npm run build` et la prod-safety ;
2. rejoue les frontières backend T1 de l'Échéancier ;
3. vérifie des invariants source Document Studio (ghost `/ai-diagnostic`, route AI, retour de `Diagnostic Établi`) ;
4. n'imprime `AUTOMATED_DOCUMENT_STUDIO_GATES_PASS` qu'après tous les gates automatisables ;
5. rappelle explicitement que clinical judgment, PDF cabinet, runtime/browser et merge/post-merge restent séparés.

Preuve disponible ici : **`bash -n scripts/certify_document_studio.sh` équivalent local = PASS**.

Le harness complet n'est pas exécuté dans le container courant : absence de checkout full-repository exact et environnement déjà connu comme différent de Python 3.12 / Node 20. Aucun PASS full-project n'est inventé.

## T2-C — tests frontend critiques versionnés

Ajoutés pour entrer dans le futur `npm test` full-project :

- `DocumentNavigationPolicy.test.ts`
  - même onglet ;
  - navigation propre ;
  - dirty Ordonnance ;
  - dirty Certificat ;
  - dirty Libre ;
  - dirty P7 ;
  - dirty accounting ;
  - Devis→Honoraires confirmation ;
  - switch accounting sans discard ;
  - Honoraires→Devis.

- `DiagnosticCompanionPolicy.test.ts`
  - normalisation acte praticien ;
  - zéro transfert sans confirmation ;
  - transfert manuel confirmé seulement ;
  - aucune copie `Diagnostic Établi`/antibiothérapie automatique dans les orientations ;
  - prix Devis neutre ;
  - instructions médicamenteuses filtrées ;
  - ligne mixte acte + médicament filtrée fail-closed.

Ces tests sont **versionnés mais leur exécution Vitest full-project n'est pas revendiquée dans cet environnement**.

## État final des pages

- P1 Ordonnance : engineering fermé ; gates clinique/runtime séparés.
- P2 Certificat : engineering convergé ; dirty-state rétabli par T1 ; runtime/PDF final différé.
- P3 Devis : CLOSED / PAUSED par décision produit ; PR #77 draft.
- P4 Note Honoraires : engineering local convergé ; PR #90 draft.
- P5 Suivi Paiement : engineering local convergé ; PR #95 draft.
- P6 Document Libre : engineering local convergé ; PR #96 draft.
- P7 Compagnon Diagnostique : engineering safety local convergé ; PR #97 draft.
- T1 Transversal : engineering transversal local convergé ; PR #101 draft.
- T2 : engineering closeout local convergé ; full recertification externe restante.

## Restes legacy non bloquants

- `DocumentFactory.create_installment_plan()` reste du code legacy interne mais le `DocumentRequest` public bloque désormais tout `type=echeancier` sous `/documents/generate` ; suppression physique possible ultérieurement après full-reference scan.
- certains registres dirty historiques restent séparés par module, mais leur orchestration est centralisée au Hub ;
- quelques props/callbacks UI historiques peuvent encore être nettoyés sans impact métier ;
- accessibilité de la modale doublon peut être alignée encore davantage avec la modale navigation.

Aucun de ces points n'est utilisé pour revendiquer une certification finale.

## Gates indispensables avant certification finale

### Automated full repository

Exécuter sur le **head candidat exact**, checkout propre, Python 3.12 / Node 20, dépendances installées :

```bash
bash scripts/certify_document_studio.sh
```

Attendre uniquement le marqueur réel :

`AUTOMATED_DOCUMENT_STUDIO_GATES_PASS`

### Runtime authentifié

Smoke P1→P7 avec patient réel :
- navigation clic + query-param et abandon brouillon ;
- preview ;
- archive ;
- reopen ;
- duplicate 409 + cancel/force ;
- impression fraîche ;
- P5 création/reload/paiement ;
- P7→P3 confirmé.

### PDF cabinet

Inspection réelle :
- Ordonnance ;
- Certificat ;
- Devis ;
- Honoraires court/long/global ;
- Échéancier ;
- Document Libre A4/A5 multi-page ;
- branding/signature/header/footer lisibles.

### Browser / responsive

Au minimum : 390 / 768 / desktop, clavier/touch/focus/dialogs.

### Validation humaine séparée

- clinique/pharmacologique Ordonnance ;
- scientifique/clinique pour toute future orientation P7 plus spécifique ;
- réglementaire si applicable au produit final ;
- financière pour flux d'encaissement si exigée par le processus de release.

### Git / release

Seulement après PASS des gates applicables :
- passer les PR requises en ready ;
- fusionner dans l'ordre de dépendance ;
- mettre à jour les canoniques master ;
- exécuter post-merge recertification.

## Conclusion

T2 clôt l'engineering local connu du Document Studio. Le prochain verrou n'est plus une correction de code connue : c'est l'exécution du harness full-repository et des certifications runtime/PDF/browser/humaines. Aucun merge ou statut production-ready n'est autorisé avant ces preuves.