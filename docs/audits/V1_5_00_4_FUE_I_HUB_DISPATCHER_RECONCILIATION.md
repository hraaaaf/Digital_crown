# V1.5-00.4 — FUE-I Hub & Dispatcher — reconciliation scoped

Date: 2026-10-08
Statut: **SOUS-LOT VALIDÉ SUR GATE CIBLÉ — 9,3/10**. Gate authentifié inter-sous-lots fin V1.5-01 : **EN ATTENTE**.

## Source canonique et périmètre

- Le closeout historique est `docs/architecture/V1_5_00_4_FINAL_INTEGRATION_AUDIT.md` : PR #724 merged le 2026-09-30 ; [Hub Visual Proof #36788607154](https://github.com/hraaaaf/Digital_crown/actions/runs/36788607154) SUCCESS et [Human Visual Approval #36790450196](https://github.com/hraaaaf/Digital_crown/actions/runs/36790450196) SUCCESS.
- Cette campagne est **FUE-I du sous-lot 00.4**, distincte du FUE-A…G général et du laboratoire PR #783. PR de réconciliation : [#803](https://github.com/hraaaaf/Digital_crown/pull/803). Elle ne prétend pas avoir testé des utilisateurs humains ni un backend clinique/PIN réel.
- Exigences : premier lancement → Hub ; les **3 destinations PC uniquement** ; persistance du mode confiée au serveur ; Centre de contrôle local accessible hors ligne ; Station lock et accès Cabinet fail-closed ; aucune donnée clinique affichée sur Hub et aucune requête sensible vers une origine externe ; message de récupération cohérent ; navigation clavier/tactile et responsive sur 390×844, 768×1024, 1280×900.

## Preuve exécutée sur le code

- **HEAD de code & workflow** : `7ec8fd6af08ed469ddff504c01a50224abc2f687`, PR #803. [Run Actions FUE 00.4 #37797275871](https://github.com/hraaaaf/Digital_crown/actions/runs/37797275871) **SUCCESS**. Le `GITHUB_SHA` du rapport est le commit virtuel de fusion `pull_request` et non le HEAD de la branche ; ne pas les confondre.
- [CI Scope Gate #37797275395](https://github.com/hraaaaf/Digital_crown/actions/runs/37797275395) **SUCCESS** ; [00.3 #37797275177](https://github.com/hraaaaf/Digital_crown/actions/runs/37797275177) **SUCCESS** ; 00.2 FUE et visual proof SUCCESS au même HEAD.
- **6 suites Vitest : 36/36 tests PASS**. **4 parcours × 3 viewports : 12/12 PASS**, **149/149 assertions navigateur**, **52 captures**, **0 page error**, **0 API backend non modélisée**, **0 requête API externe inattendue**, **0 overflow horizontal**, **0 contrôle interactif hors écran à zoom texte 200 % sur mobile**.
- Artefact GitHub [#11559226714](https://github.com/hraaaaf/Digital_crown/actions/runs/37797275871/artifacts/11559226714), SHA-256 ZIP : `635e80eb362a4ccdc7e27148df8a427a5cbb3a961f4f84124f7b2543b0ead659` ; **52 PNG + 13 JSON = 65 fichiers**. `certification-matrix.json` et chaque journal de scénario inspectés.

## Matrice AVANT / ACTION / APRÈS

| Parcours réel navigateur (API workstation simulée explicitement) | Vérification | Résultat |
| --- | --- | --- |
| `fresh-routing` | Hub vierge, exactement 3 cartes Cabinet/Station/Control ; pas de données/requêtes métier ; navigation clavier vers Control Center et retour ; refus Station non appairée ; Cabinet anonyme vers Login, URL Dashboard directe rejetée ; 200 % texte mobile | 3/3 PASS |
| `offline-recovery` | Hub et Control accessibles avec bootstrap 503 ; alertes de récupération lisibles sans toast 500 contradictoire ; HTTP LAN interdit, origine HTTPS distante non sondée avant action ; retour Hub ; Dashboard clinique anonyme refusé | 3/3 PASS |
| `locked-station` | mode serveur mémorisé Station ; refus Hub/Control par URL directe ; verrou persistant après rechargement | 3/3 PASS |
| `remembered-control` | dispatch automatique Control ; rechargement ; sélection volontaire `/hub?select=1` honorée | 3/3 PASS |

## Défauts observés et réparés

1. **Laboratoire (fausse classification, non défaut runtime) :** les téléchargements Google Fonts CSS/WOFF étaient pris à tort pour des appels cliniques à une origine externe. Le harness distingue les seuls domaines et types de ressources fonts autorisés et vérifie l'absence de cookie/Authorization ; toute autre origine externe reste bloquante.
2. **P2 UX — runtime corrigé :** le bootstrap Workstation 503 provoquait un toast `Erreur Serveur (500)` redondant avec l'information de récupération du Hub et du Centre de contrôle. `frontend/src/services/api.ts` ne montre plus ce toast générique **uniquement** pour `/workstation/bootstrap` et `/workstation/state` sur `/hub` ou `/control-center` lors d'un 503 ou défaut réseau ; toutes les erreurs cliniques et autres erreurs restent signalées. Assertions dédiées browser et capture AFTER confirment l'absence de toast contradictoire.
3. **Harness — classification stricte de la panne volontaire :** le logger Axios émet `Path: /workstation/bootstrap` et `Details: offline-proof` pour le 503 explicitement injecté ; seuls ces messages exacts du scénario offline sont exclus des erreurs inattendues. Aucune exclusion générique d'une erreur JS.
4. Deux tests Vitest ajoutés à `WorkstationModeGate.test.tsx` : accès clinique bloqué quand l'autorité est indisponible et dispatch Cabinet mémorisé sur serveur.

## Contre-revue adversariale interne (deux perspectives, même HEAD testé)

### A — UX / accessibilité (impasses, clics, images falsifiées)

- Les captures AVANT/APRÈS de chacun des 12 parcours confirment les transitions et la récupération hors ligne ; le Centre de contrôle reste accessible, la destination clinique sans autorisation renvoie au Login, Station ne se contourne pas.
- Un problème P2 du toast de panne a été **observé en capture initiale**, corrigé et revérifié. L'écran Hub offline AFTER comporte son message explicite, sans toast superposé.
- Sur mobile à 200 % texte, boutons visibles et aucun overflow détecté, mais le texte des cartes est **dense / fortement replié**, avec un long défilement. **Dette P2 de finition accessibilité**, non bloquante pour cette première certification et à traiter en polish transversal UX, sans préjuger d'un audit WCAG complet.
- Score scope UX sévère : **9,1/10**.

### B — Safety / contrat / preuve (fail-open, authentification simulée, faux vert)

- Les états Workstation sont explicitement simulés dans le runner Vite seul, avec interceptions nominatives; toutes les APIs cabinet non modélisées échouent, toute origine distante non autorisée est enregistrée/bloquante, les requêtes Fonts tiers ne contiennent ni Authorization ni Cookie selon les observations du navigateur.
- `/dashboard` reste inaccessible à un utilisateur anonyme (y compris depuis le Hub offline), Station ne s'ouvre pas sur un poste non appairé et empêche les contournements directs d'une Station verrouillée.
- **NON TESTÉ dans 00.4** : authentification clinique vraie, PIN serveur, cookie/tenant/revocation réels, changement de poste physique/reboot et intégration transverse. Obligatoire dans le **gate réel de fin V1.5-01**, pas un PASS implicite.
- Le runner précédent était rouge pour des logs attendus ; le nouveau résultat vert ne vient pas d'une désactivation de fail-closed ni d'un changement de serveur.
- Score contrat/fail-close scoped : **9,5/10**.

### Verdict et suite

**Score cible retenu : 9,3/10 sur le gate FUE-I 00.4 scoped** (UX 9,1 ; contrat 9,5 ; moyenne 9,3), **0 BLOCKER/MAJOR restant** dans le périmètre effectivement exécuté. **Deux revues internes**, aucune revue indépendante externe prétendue. Historique et validation technique de 00.4 réconciliés sans modifier le backend.

**Ne pas prononcer « FUE intégrée CONVERGED »** : le backend authentifié et le PIN restent à valider en fin de V1.5-01, décision utilisateur maintenue. **Aucun merge ni déploiement**. Next : progresser vers les sous-lots V1.5-01 tout en conservant dette P2 mobile texte 200 % ; préparer puis exécuter le gate transverse réel en fin de lot.
