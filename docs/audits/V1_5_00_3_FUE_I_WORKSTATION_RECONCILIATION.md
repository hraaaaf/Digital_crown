# V1.5-00.3 — FUE-I Workstation mode — inventory

Date: 2026-10-08
Statut: DÉMARRÉ — preuves en réconciliation, pas encore validé.

## Scope
Première utilisation d'un poste : identité workstation opaque / mémorisation mode, changement contrôlé, réouverture/restart, retour Hub, sécurité Station, récupération après erreur, cloisonnement Cabinet/Mobile/Companion. PR #783 = laboratoire à adapter, pas certificat FUE.

## Preuve historique source
`docs/architecture/V1_5_00_3_WORKSTATION_MODE_REVIEW.md` décrit autorité serveur, escape PIN lié à identité/tenant/session/revision/expiration, protection HTTP et WebSocket, ainsi que tests 67 backend + 19 frontend et captures 4 états × 3 viewports. Son en-tête est **CLOSEOUT CANDIDATE** au moment de la rédaction : vérifier merge/CI exact-head et artefacts historiques avant de réutiliser la preuve. Aucun score FUE encore attribué.

## Gate propre au sous-lot
Tester tous les éléments du mode workstation applicables : poste nouveau/configuré, défaut cabinet, mode Station verrouillé, navigation et retour Hub, changement autorisé, erreur PIN, expiration, session révoquée, redémarrage et messages intelligibles; captures avant/action/après et matrice PASS/FAIL/NON TESTÉ. Ne bloquer que sur rouge significatif prouvé ou invariant critique non prouvé.

## Gate transversal fin lot 01
Validation réelle inter-modules Cabinet authentifié + Station appairée + serveur PIN/recovery pourra être réconciliée en fin V1.5-01; ne pas l'attribuer prématurément au gate 00.3.

Next : retrouver PR et run exact-head 00.3, inspecter artifacts, adapter workflow Actions seulement sur manque constaté. Aucun merge ni déploiement.
