# FUE-G03 — Phase A3 — rendez-vous, accueil staff et Wall Display

**État : PRE / FUE-0 DOCUMENTAIRE UNIQUEMENT / NON CERTIFIÉ.** Autorisation propriétaire « Bon allez je valide on peut passer mnt a A3 !? » du 24/10/2026. Cette autorisation déclenche le **cadrage isolé** d'A3. Elle ne renomme pas A2 GREEN et n'autorise aucun merge, déploiement, mutation clinique ou contournement GitHub Actions.

## 1. Dépendances, HEAD et règle de séparation

- **Base git documentée** : A1 [PR #1066](https://github.com/hraaaaf/Digital_crown/pull/1066), HEAD exact `0664393ec36fbecf7d3dd5108d80b6aebf1b5e75`, statut LAB A1 GREEN, PR DRAFT. A3 est une PR distincte de documentation basée sur ce HEAD ; elle **n'empile pas** le travail non certifié d'A2.
- **A2** : [PR #1069](https://github.com/hraaaaf/Digital_crown/pull/1069), HEAD `4e6badcb149884e60d78a2c4f28d953b17cbc476`, OPEN/DRAFT et **pas de workflow E2E A2**. Approbation conversationnelle != run ni validation des captures. Cette dette est un **gate de dépendance pour clore A3** et pour tout déploiement/merge qui la consommerait.
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

1. **D'abord** : résoudre A2 sans lever les protections : approbation du workflow dédié par voie GitHub autorisée, exécution E2E A2 exacte HEAD, révision des PNG et oracle SQL; si blocage, garder A2 OPEN et A3 au stade PRE.
2. **Puis** : vérifier qu'aucun des cas A3 n'est déjà prouvé sur le candidat A3 HEAD avant de lancer de nouvelles campagnes; produire seulement le Delta E2E pertinent. Ne pas recopier les scripts 03.21 ni réexécuter toutes les suites sans raison.
3. **Exécuter** en laboratoire SQLCipher exclusivement fictif : un vrai poste patient (Station), un poste accueil Cabinet authentifié et un Wall indépendant dans Chromium. API FastAPI réelle, preuves HTTP négatives, audits SQL indépendants, captures avant/après (identité bornée, assistance, appels, résilience). Enregistrer SHA exact, URL CI, nombre de tests, fichiers/empreinte d'artefact. Tout résultat absent = NOT_RUN, tout échec critique = RED.
4. **Clore après preuve** : audit risques de données/patient, vérification visuelle humaine **sur les captures réelles A3**, verdict FUE/RPG final et dépendance A2 sans REQUIRED rouge. En l'absence d'un de ces contrôles : A3 OPEN, aucune mention GREEN ni merge.

## 5. Exclusions et limites

A3 ne couvre pas l'identification QR/Companion A1, l'identification secours A2, le contrôle d'un véritable lecteur NFC/caméra, le kiosque physique Windows, le LAN/TLS cabinet, les imprimantes, la mise en service clinique, un merge ou un déploiement. **G03-22 / LOT10** restent physiques OPEN. La famille B résilience et les phases C/D ne sont pas activées par ce cadrage.

## 6. État de préparation

**FUE-0 préparé / CI A3 NOT_RUN / A3 E2E NOT_RUN / captures A3 NOT_AVAILABLE / score non attribué.** Next : clôture technique d'A2 puis construction/exécution du delta A3. Ce document est une matrice PRE et non une certification exécutable.
