# techdoubt.md — Crown Bot CB-01 / FIRST_VALUE_UI

Ce registre contient uniquement des réserves **CB-01** encore non levées. Les tests physiques sont réservés au **Lot 10**, pas à cette mission logicielle.

## CB01-TD-20261018-01 — S01 après correction du contrat horaire — OUVERT
- **Observation** : [run #39128715548](https://github.com/hraaaaf/Digital_crown/actions/runs/39128715548) sur `f0b544af364fb905573765a6db27c7fbc771c69a` avait 6/7 workflows applicables SUCCESS, **CB-01 RED** à l'étape S01 (Code `UNEXPECTED_TRANSPORT_OR_RUNTIME`). L'inspection du [script S01](https://github.com/hraaaaf/Digital_crown/blob/f0b544af364fb905573765a6db27c7fbc771c69a/frontend/scripts/certify-cb01-s01-s12-matrix.mjs#L222-L240) a montré que l'assertion attendait `toISOString()` avec suffixe Z, alors que le correctif Agenda convertit maintenant le jour au contrat **heure locale sans timezone**. Le run Chromium d'acceptation sidecar a lui-même affiché `CB01_ASSOCIATE_SIDECAR_VISUAL: PASS` et Windows/PostgreSQL CB-01 SUCCESS.
- **Correction posée** : script S01 importe dans le navigateur le module produit `formatAgendaWallClock` et vérifie les bornes d'Agenda de demain à la milliseconde près, via la même requête HTTP. Aucun assouplissement des droits, de la date attendue ni de la détection d'écritures.
- **Réserve** : la nouvelle CI du HEAD contenant la correction n'était pas terminée à la vérification ; **ne pas déclarer ALL GREEN ni CONVERGED** sans résultats/artefacts sur le SHA final. Exécuter la CI (déjà déclenchée), diagnostiquer/corriger tout nouveau RED, vérifier le HEAD exact.
- **Classification** : CB-01 logiciel / experimental CB-01 Visual ; bloquant de convergence si RED réel sur final HEAD.

## CB01-TD-20261018-02 — Preuves et revues restantes — OUVERT
- Les 5 défauts de revue adversariale (horaires Agenda, historique texte, filtre praticien fail-closed, accessibilité dialog, premier clic Chromium) sont corrigés en code dans [PR #904](https://github.com/hraaaaf/Digital_crown/pull/904), mais **régression finale à prouver** sur le HEAD actuel.
- Zoom navigateur **natif 200 %** non prouvé : test actuel de réduction CSS de largeur seulement. Tests lecteurs d'écran/contrastes complets non certifiés. CB-01 dispose de 0 revues GitHub par deux personnes indépendantes, donc **CONVERGED=NON** même si CI GREEN.
- **Actions** : valider vrais jobs de CI, ajouter si nécessaire tests UX logiciels, demander 2 reviewers réels sur un HEAD stable ; revue interne A/B du même assistant ≠ revue indépendante.
- **Hors scope** : ne pas déplacer l'essai humain physique/T2 du Lot 10 vers CB-01.
