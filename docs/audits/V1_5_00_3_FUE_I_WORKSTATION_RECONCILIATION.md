# V1.5-00.3 — FUE-I Workstation mode — inventory

Date: 2026-10-08
Statut: **GATE TECHNIQUE/VISUEL DU SOUS-LOT VALIDÉ** — FUE intégrée fin lot V1.5-01 EN ATTENTE.

## Scope
Première utilisation d'un poste : identité workstation opaque / mémorisation mode, changement contrôlé, réouverture/restart, retour Hub, sécurité Station, récupération après erreur, cloisonnement Cabinet/Mobile/Companion. PR #783 = laboratoire à adapter, pas certificat FUE.

## Preuve historique source
`docs/architecture/V1_5_00_3_WORKSTATION_MODE_REVIEW.md` décrit autorité serveur, escape PIN lié à identité/tenant/session/revision/expiration, protection HTTP et WebSocket, ainsi que tests 67 backend + 19 frontend et captures 4 états × 3 viewports. Son en-tête est **CLOSEOUT CANDIDATE** au moment de la rédaction : vérifier merge/CI exact-head et artefacts historiques avant de réutiliser la preuve. Aucun score FUE encore attribué.

## Gate propre au sous-lot
Tester tous les éléments du mode workstation applicables : poste nouveau/configuré, défaut cabinet, mode Station verrouillé, navigation et retour Hub, changement autorisé, erreur PIN, expiration, session révoquée, redémarrage et messages intelligibles; captures avant/action/après et matrice PASS/FAIL/NON TESTÉ. Ne bloquer que sur rouge significatif prouvé ou invariant critique non prouvé.

## Gate transversal fin lot 01
Validation réelle inter-modules Cabinet authentifié + Station appairée + serveur PIN/recovery pourra être réconciliée en fin V1.5-01; ne pas l'attribuer prématurément au gate 00.3.

Next : traiter V1.5-00.4 en FUE de sous-lot; intégration réellement authentifiée et serveur PIN reportées à fin V1.5-01. Aucun merge ni déploiement.

## POST — Gate scoped du sous-lot 00.3 — 2026-10-08

- PR #803, HEAD produit/testé `227efdabc9ead0d6660fca0a5794bd397af9a053` : [run FUE #37785705010](https://github.com/hraaaaf/Digital_crown/actions/runs/37785705010) **SUCCESS** ; CI Scope Gate SUCCESS ; FUE 00.2 SUCCESS sur même HEAD.
- Quatre suites Vitest **21/21 PASS** : Hub routing 4, WorkstationModeGate 7, WorkstationModeAdminPanel 5, WorkstationIdentityPanel 5.
- Artefact #11554880976 digest SHA256 `2b5afaecce95aad9f7b0c45b9f00318c283ba5be39dee57a8e4ef3799b5ad0b7` : `report.json` + **12 PNG**, exactement 4 états (hub-admin / hub-enroll / station-locked / station-admin) sur 390×844, 768×1024, 1280×900.
- Matrice effective 12/12 expectedVisible, **0 erreur console/page**, **0 API non modélisée**, **0 overflow**. Rapport `commit=dad464ad…` correspond au SHA de la ref synthétique `pull_request` Actions ; utiliser le commit HEAD PR ci-dessus pour la preuve de code, pas le `GITHUB_SHA` du merge-ref.
- Examen visuel des captures mobile : Station verrouillée claire, CTA de demande d'aide et PIN d'administration lisibles ; Hub d'admin long en hauteur, densité perceptible sur petit écran. Pas de BLOCKER/MAJOR démontré par ces images ; éventuelle simplification UX mobile P2.

### Revue adversariale interne, deux perspectives

| Check | Preuve / appréciation | Score sévère |
|---|---|---:|
| Contrats Hub / Workstation (4 suites) | 21/21 PASS ; API vraie non sollicitée | 8.5/10 |
| UI responsive + états visibles | 12/12 PNG et aucune overflow, interaction limitée | 8.0/10 |
| Détection de pannes / régressions harness | Les requêtes backend inconnues fail-closed ; 0 erreur, 0 unexpected | 8.5/10 |
| UX first-use réellement jouée | états prépositionnés, presque aucun clic ; cible d'intégration différée | 6.5/10 |
| Auth/PIN/reprise réelle intégrée | **NON TESTÉ dans ce gate** (fin lot 01), pas noté | N/A |

**Perspective UX** : pas d'impasse dans les états statiques montrés ; insuffisance de preuve de parcours click-through, **amélioration de couverture à fin lot 01**. **Perspective safety/contrat** : routes backend explicitement simulées selon les interfaces et route inconnue signalée ; pas de prétention à validation serveur ni à sécurité réelle du PIN. **Score prudent du gate ciblé : 8.0/10** (n'inclut pas la FUE intégrée). Revue indépendante externe non réalisée. Le statut 'CONVERGED FUE-G' n'est donc **pas** prononcé.

**Verdict** : sous-lot 00.3 **VALIDÉ sur son gate automatisé scoped**, mais la certification FUE-G inter-sous-lots et ses preuves serveur restent **EN ATTENTE jusqu'à la fin de V1.5-01** conformément à la décision de périmètre. Ne pas réinterpréter le succès de mocks comme test serveur. Aucun merge/déploiement.
