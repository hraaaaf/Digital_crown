# FUE-G03 — Phase A3 — rendez-vous, accueil staff et Wall Display

**État : PRE / FUE-0 DOCUMENTAIRE UNIQUEMENT / NON CERTIFIÉ.** Autorisation propriétaire « Bon allez je valide on peut passer mnt a A3 !? » du 24/10/2026. Cette autorisation déclenche le **cadrage isolé** d'A3. Elle ne renomme pas A2 GREEN et n'autorise aucun merge, déploiement, mutation clinique ou contournement GitHub Actions.

## 1. Dépendances, HEAD et règle de séparation

- **Base git documentée** : A1 [PR #1066](https://github.com/hraaaaf/Digital_crown/pull/1066), HEAD exact `0664393ec36fbecf7d3dd5108d80b6aebf1b5e75`, statut LAB A1 GREEN, PR DRAFT. A3 est une PR distincte de documentation basée sur ce HEAD ; elle **n'empile pas** le travail non certifié d'A2.
- **A2 (candidat courant)** : [PR #1079](https://github.com/hraaaaf/Digital_crown/pull/1079), HEAD vérifié au 24/10/2026 `9c9b459010921313e8cc81f9479ba2a759df3585`, OPEN/DRAFT. Preuve indépendante **LAB MANUEL PASS** : 39 pytest + 28 Vitest, vrai Chromium→FastAPI→SQLCipher, 10 PNG SHA-256, correctifs 403/429 confirmés. Le propriétaire a accepté les **deux écrans UX corrigés**, mais **le workflow E2E GitHub Actions officiel dédié est absent/protégé et reste requis avant certification**. L'ancienne [PR #1069](https://github.com/hraaaaf/Digital_crown/pull/1069) est historique, non la base d'exécution retenue. A3 reste une PR **PRE séparée**, ne consomme pas les commits non certifiés d'A2.
- **Preuve antérieure réutilisée, pas rerunée** : [G03.21 CI #40090283557](https://github.com/hraaaaf/Digital_crown/actions/runs/40090283557), HEAD `44625de39cbff8e82424bc59faa4dc0af45a014d`, 4/4 jobs SUCCESS. [Artefact intégré #12558614110](https://github.com/hraaaaf/Digital_crown/actions/runs/40090283557/artifacts/12558614110) : 12 vrais PNG Chromium et `seed.json`, `evidence-after.json`, `sql-after.json` ; deux postes Station distincts et acteur accueil Cabinet, backend FastAPI local + SQLCipher jetable. À 0 RDV : staff assistance et ACK; à 1 RDV : arrivée explicite + appel Wall n°307; à 2 RDV : premier choisi et arrivé, second laissé PREVU, appel Wall n°308. **Ceci valide uniquement G03.21 LAB sur son ancien HEAD**, ni les négatifs A3, ni le physique.
- **Autres preuves existantes, à ne pas dupliquer mécaniquement** : `backend/tests/test_station_patient_session_v15.py` couvre déjà la sélection de RDV, isolation patient/date, idempotence, permissions staff, ticket explicite/collisions, modes d'identité Wall, ACK, limites publiques. Les tests React `StationAppointmentArrival` et `StationWallDisplay` couvrent certains états d'affichage, à réexaminer au SHA testé.

## 2. Goal utilisateur et oracle métier

Sur une borne Station d'un cabinet fictif, un patient déjà identifié doit pouvoir consulter **seulement ses RDV du jour**, choisir explicitement le bon lorsque N>1, confirmer une arrivée persistante exactement une fois ou demander le personnel si 0. La réception doit recevoir et acquitter les demandes; elle seule déclenche l'appel; le Wall public indépendant doit afficher l'identité **strictement bornée par la configuration** sans notes médicales ou données d'un autre cabinet. Un réseau interrompu, des réponses obsolètes, un poste révoqué et des appels invalides ne doivent ni inventer une arrivée ni afficher une ancienne identité.

## 3. Matrice A3 : compléter les lacunes, pas répéter G03.21

| Cas | Situation / acteur | Oracle vérifiable | Preuve et portée |
| --- | --- | --- | --- |
| A3-01 / G03-10/11/12 | 0/1/N RDV après identité confirmée | 0 => assistance staff; 1 => arrivée explicite; N => sélection forcée, seul RDV choisi muté | **Déjà prouvé G03.21** sur ancien HEAD ; ne rouvrir que si dépendance invalidée |
| A3-02 / G03-13 | RDV d'un autre patient, autre date, supprimé ou état non éligible | 404/409 générique selon route; aucun changement SQL ni divulgation | Tests backend déjà existants; ajouter E2E HTTP ciblé si lacune démontrée |
| A3-03 / G03-14 | Double confirmation, retry/réponse concurrente | idempotence; 1 seul changement/audit; ticket préservé; aucune arrivée supplémentaire | Comparer réponses API à SQL indépendant sur base jetable |
| A3-04 / G03-15 | API indisponible pendant arrivée puis rétablie | message d'échec vrai, aucun succès mensonger, reprise propre; pas de contenu patient conservé après reset | Chromium réels + API contrôlée sur runner isolé, snapshots BEFORE/AFTER |
| A3-05 / G03-19 | 0 RDV, assistance staff répétée, ACK répété et autres tenants | alerte unique, ACK unique, staff autorisé, aucune fuite du feed | E2E multi-acteurs Station/accueil et SQL `AuditLog` |
| A3-06 / G03-16 | Appel staff depuis bonne/ mauvaise identité et permissions | Station non autorisée / RBAC refusé 403/423; cabinet étranger 404; aucune mutation Wall | Vrais cookies distincts et connexion staff, oracles HTTP+SQL |
| A3-07 / G03-17 | Wall `initials`, `full_name`, `number_only`, liste bornée | seules les informations configurées; jamais dossier, téléphone, soin, motif, secret | Wall Chromium + configuration cabinet fictive + inspection texte/PNG |
| A3-08 / G03-18 | Ancienne réponse Wall, coupure, TTL dépassé, reconnect | réponse périmée ignorée; panne visible sans faux état « aucun patient »; ancien appel disparaît | Vrais traitements frontend + contrôle horloge/SQL test-only; pas de fictif « PASS » |
| A3-09 / G03-16 | Appel invalide : ticket manquant, hors plage, doublon, RDV non en attente | 409/404 selon contrat; pas d'appel audit supplémentaire | Contrat backend + requêtes réelles staff → Wall → oracle SQL |
| A3-10 / G03-20 | Arrivée Station sans preuve staff de présence | aucun reçu de présence clinique autorisé par simple check-in | Régression backend existante + oracle documentaire |
| A3-11 / G03-09/18 | Révocation Station, changement patient, purge/retour Hub, réponse tardive | aucune donnée patient persistante sur borne ou Wall après invalidation | tests réels négatifs, screenshots AFTER des écrans neutres |
| A3-12 / UX | FR/EN/AR RTL, 390/430/768/1280, texte 200 %, clavier | actions accessibles sans débordement ni fuite, pas de pageerror | captures BEFORE/ACTION/AFTER sur uniquement surfaces A3 existantes |

## 4. Exécution future et conditions d'arrêt

1. **D'abord** : lever le **dernier gate officiel A2** sans contourner les protections : approbation du workflow dédié via GitHub autorisé, exécution CI au HEAD courant exact et revue des logs/PNG/SQL. Le laboratoire manuel et l'accord visuel sur deux AFTER sont déjà probants mais **ne suffisent pas** à clôturer le gate. Si CI bloquée, maintenir A2 OPEN et A3 PRE.
2. **Puis** : vérifier qu'aucun des cas A3 n'est déjà prouvé sur le candidat A3 HEAD avant de lancer de nouvelles campagnes; produire seulement le Delta E2E pertinent. Ne pas recopier les scripts 03.21 ni réexécuter toutes les suites sans raison.
3. **Exécuter** en laboratoire SQLCipher exclusivement fictif : un vrai poste patient (Station), un poste accueil Cabinet authentifié et un Wall indépendant dans Chromium. API FastAPI réelle, preuves HTTP négatives, audits SQL indépendants, captures avant/après (identité bornée, assistance, appels, résilience). Enregistrer SHA exact, URL CI, nombre de tests, fichiers/empreinte d'artefact. Tout résultat absent = NOT_RUN, tout échec critique = RED.
4. **Clore après preuve** : audit risques de données/patient, vérification visuelle humaine **sur les captures réelles A3**, verdict FUE/RPG final et dépendance A2 sans REQUIRED rouge. En l'absence d'un de ces contrôles : A3 OPEN, aucune mention GREEN ni merge.

## 5. Exclusions et limites

A3 ne couvre pas l'identification QR/Companion A1, l'identification secours A2, le contrôle d'un véritable lecteur NFC/caméra, le kiosque physique Windows, le LAN/TLS cabinet, les imprimantes, la mise en service clinique, un merge ou un déploiement. **G03-22 / LOT10** restent physiques OPEN. La famille B résilience et les phases C/D ne sont pas activées par ce cadrage.

## 6. État de préparation

**FUE-0 préparé / CI A3 NOT_RUN / A3 E2E NOT_RUN / captures A3 NOT_AVAILABLE / score non attribué.** Next : clôture technique d'A2 puis construction/exécution du delta A3. Ce document est une matrice PRE et non une certification exécutable.


## 7. Delta A3 vérifié sur le code — préparation ciblée du 24/10/2026

**Base de lecture : A1 \`0664393ec36fbecf7d3dd5108d80b6aebf1b5e75\` ; aucune campagne A3 nouvelle exécutée.** L'accord propriétaire « Vas y do it » après acceptation des deux écrans UX A2 autorise à avancer la **préparation** A3 en parallèle, sans prétendre que les gates A2 sont levés.

### Couverture déjà existante — ne pas réinventer les tests

- Backend : \`backend/tests/test_station_patient_session_v15.py\` contient explicitement \`test_station_today_bridge_zero_single_multiple_and_day_scoping\`, \`test_station_today_bridge_excludes_other_patient_and_deleted\`, \`test_station_arrival_sets_existing_waiting_status_is_idempotent_and_preserves_ticket\`, \`test_station_arrival_fails_closed_for_ineligible_status\`, \`test_station_arrival_cannot_target_other_patient_or_other_day\`, \`test_no_appointment_staff_assistance_is_durable_idempotent_and_acknowledgeable\`, \`test_staff_assistance_feed_requires_agenda_permission\`, \`test_wall_display_is_pseudonymous_shared_and_call_is_bounded\`, \`test_wall_display_caps_public_identifiers_but_keeps_total_count\` et \`test_wall_call_requires_waiting_state_and_unique_explicit_ticket\`.
- Interface : \`frontend/src/features/hub/StationAppointmentArrival.test.tsx\` couvre zéro RDV et signal staff en échec, arrivée unique explicite, sélection de plusieurs RDV, échec d'écriture, contrastes et textes EN/AR. \`frontend/src/features/hub/StationWallDisplay.test.tsx\` couvre \`initials\`, \`full_name\`, \`number_only\`, limite de huit, chargement initial non trompeur, appel et réponses poll obsolètes / indisponibles.
- Laboratoire intégré **G03.21** : \`frontend/scripts/certify-v15-03-real-station-wall-integrated.mjs\` est déjà passé dans la CI à **l'ancien** HEAD \`44625de39cbff8e82424bc59faa4dc0af45a014d\` [run #40090283557](https://github.com/hraaaaf/Digital_crown/actions/runs/40090283557) avec 12 vrais PNG ; trois parcours RDV et deux appels 307/308 avec acteur réception distinct. Cette preuve n'est pas transposable automatiquement au futur HEAD A3.

### Plan de vérification de l'écart (ordre de priorité après gate A2)

1. **A3-P1/Réseau et concurrence (A3-03/A3-04/A3-08)** : maintenir un retour API d'arrivée en attente pendant un reset Station, puis restituer une réponse tardive ; générer simultanément ACK/appel staff et une lecture Wall tardive ; vérifier absence de réapparition d'identité, de double mutation et de « salle vide » trompeur. Capturer des BEFORE/ACTION/AFTER Chromium indépendants et des états SQL avant/après.
2. **A3-P1/RBAC et cloisonnement (A3-05/A3-06/A3-09)** : actor cookies distincts Station, réception avec/sans agenda, Wall, cabinet étranger ; requests HTTP refusées 401/403/404/409 selon contrat réel, et compteurs SQL/AuditLog inchangés sur les refus. Ne jamais contourner les permissions avec un profil admin commun dans les tests négatifs.
3. **A3-P1/Confidentialité et révocation (A3-07/A3-11)** : comparer les rendus réels du Wall \`initials/full_name/number_only\`, ancien appel TTL expiré, absence notes/motif/téléphone, borne reset et sessions révoquées, avec six captures ciblées, au moins une après effacement.
4. **A3-P2/UX d'accessibilité (A3-12)** : documenter FR/EN/AR RTL, clavier, zoom 200 %, 390/430/768/1280 ; si une régression prouvée touche l'accessibilité ou la confidentialité, corriger dans une PR de code distincte, et ne pas la faire passer pour simple retouche documentaire.

### Contrat de preuves avant exécution

- Chaque scénario donne un identifiant stable, acteur, entrée synthétique, action observée, code HTTP, oracle SQL indépendant, image PNG, empreinte SHA-256 et commit \`EVALUATED_SHA\`. Un scénario manquant est **NOT_RUN**, pas PASS.
- Les séquences E2E / captures A3 ne se déclenchent pas automatiquement à la création de cette documentation. Aucun compte réel, dossier clinique réel, infrastructure du cabinet, LOT10, matériel ni production.
- **Ordre obligatoire : A2 CI certifié → A3 delta exécuté au HEAD exact → revue visuelle humaine A3 → verdict A3**. A3 peut préparer ses fixtures et son plan pendant le blocage CI A2, mais ne déclare jamais « A3 GREEN » sur cette base documentaire.


## 8. Gate A2 levé — lancement d'A3 autorisé (25/10/2026)

**La dépendance bloquante A2 a été levée et vérifiée sur GitHub** au commit `972eba4cbed824d97f0eee01d48cbd0a3bedba37`, [PR #1079](https://github.com/hraaaaf/Digital_crown/pull/1079). [E2E Chromium / FastAPI / SQLCipher #40178655899](https://github.com/hraaaaf/Digital_crown/actions/runs/40178655899) = `success`; [CI Scope #40178655906](https://github.com/hraaaaf/Digital_crown/actions/runs/40178655906) = `success`; [Hub Visual Proof #40178655895](https://github.com/hraaaaf/Digital_crown/actions/runs/40178655895) = `success`; [Human Visual Approval exact HEAD #40181754812](https://github.com/hraaaaf/Digital_crown/actions/runs/40181754812) = `success`. Le label propriétaire `visual-approved-by-achraf` est présent. Le retrait de « Station sécurisée » est inclus et vérifié. **A2 est certifié techniquement et visuellement, mais non fusionné.**

**Nouvel ordre d'exécution demandé par le propriétaire** : « Allez A3 ! ». A3 passe de *PRE bloqué par A2* à *préparation d'exécution autorisée*. Il ne devient pas certifié sans tests A3 au SHA final, SQL indépendant, vrais écrans et approbation humaine A3 propre.

**Règle de branchement :** le code A3 en laboratoire doit partir du HEAD A2 certifié (ou être explicitement empilé dessus), tandis que la PR documentaire #1076 reste volontairement ancrée sur A1. Une validation G03.21 ancienne ne remplace pas les scénarios négatifs A3 actuels. Aucun merge, déploiement ou dossier réel.

**Critères d'entrée A3** : cas P1 A3-03/04/05/06/07/08/09/11 prioritaires ; trois acteurs isolés (Station, réception staff, Wall) ; jeu fictif exclusivement ; tests contrôlés des données affichées en public, retard de réponse, reprise, révocation, appels non autorisés et idempotence. Les preuves doivent indiquer chaque cas testé ou `NOT_RUN` ; interdiction de « GREEN » global si les oracles exigés manquent.
