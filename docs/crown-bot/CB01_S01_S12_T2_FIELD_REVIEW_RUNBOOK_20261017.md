# Digital Crown — CB-01 / CB-00 — terrain S01–S12 et revue adversariale

**Date :** 2026-10-17. **Statut :** guide d'exécution, pas certificat terrain ni permission de déployer.  
**PR cible :** [#904](https://github.com/hraaaaf/Digital_crown/pull/904) (draft, base #903).  
**Scope :** Crown Bot Cabinet Web Desktop uniquement ; Pocket « En cours de construction ». Aucun patient réel, action clinique, activation de flag prod, fusion ou déploiement autorisés par ce guide.

## 1. Deux types de preuve qui ne se remplacent pas

La CI Ubuntu + Chromium exécute, sur base SQLite jetable isolée, les contrats HTTP S02/S03/S04/S05/S06/S08/S11 et le parcours navigateur S01 **Agenda → Jour → lendemain**. Le fichier d'artefact `s01-s12-synthetic-matrix.json` fait foi seulement pour le SHA contenu dans `exactHead`. Les tests S07/S09/S10/S12 pouvant apparaître dans d'autres gates (concurrence, Vitest) **ne deviennent pas automatiquement des parcours UI humains CB-01 PASS**.

Le contrôle métier réel nécessite le poste **DESKTOP-3MAJEEH** reconnecté, isolé, expressément autorisé, avec identités/tenants fictifs. Ce poste était OFFLINE lors du dernier contrôle. Pas de synchronisation des données d'un cabinet réel.

### Alternative GitHub Actions si DESKTOP-3MAJEEH est hors ligne

La [CI expérimentale CB-01](https://github.com/hraaaaf/Digital_crown/actions/workflows/cb01-associate-sidecar-visual.yml) exécute un job **Ubuntu/Chromium synthétique** avec fausses identités et fixtures jetables, ainsi qu'un job **Windows hébergé GitHub**. Ce dernier lance sous Windows les suites Vitest JSDOM MainLayout, CrownBotWorkflowPreview, CrownBotChat, GhostBrainWidget S12 et AgendaModal S10 ; il vérifie le SHA exact de la PR, impose un ensemble complet de tests, conserve JSON + attestation comme artefact, et atteste explicitement **0 parcours humains**, **zoom navigateur natif non exécuté**, **cabinet clinique non utilisé**. Ces jobs permettent de continuer à coder et qualifier les régressions Windows sans attendre le poste T2.

**Règle de preuve :** un runner Windows n'est pas le poste du cabinet. Un test JSDOM ne mesure ni le navigateur Windows avec zoom natif 200 %, ni l'accessibilité observée par un praticien, ni les interactions S01–S12 end-to-end. Les screenshots Chromium Ubuntu sont synthétiques (390/430/1280/1440/1600/1920) ; aucune validation humaine n'en résulte. Les deux reviewers humains indépendants et les traces opérateurs restent requis par le gate CONVERGED, quel que soit le nombre de workflows GREEN. Ne pas activer Pocket, ne pas activer de flag en production et ne pas simuler de preuve humaine.

## 2. Préalables fail-closed

1. Lire HEAD de #904 et #903 et vérifier le SHA du binaire T2 effectivement exécuté ; aucune extrapolation à partir d'un vieux run.
2. Station T2 Windows isolée, localhost autorisé et données fictives uniquement, credentials synthétiques masqués, double opt-in Crown Bot appliqué au T2 **seulement**. Contrôler l'enrôlement propre du poste par les API normales, sans désactiver les verrous HTTP 423.
3. Snapshot base **complète** et audit : tables, nombre de rendez-vous, BotPendingAction, patients, devis, échantillons, alertes ; distinguer les écritures techniques attendues (auth/workstation) des écritures cliniques interdites. Conserver rapport diff après exécution.
4. BEFORE sur **1280×900, 1440×900, 1600×900, 1920×900** et zoom navigateur **natif 200 %** ; vérifier même profil/fenêtre/cabinet/date/rôle pour AFTER. Le proxy 800/960 px de GitHub n'est PAS le zoom natif.
5. Mesurer 30 lectures utiles successives par scénario, p50/p95 click-to-useful-DOM et HTTP ; ne pas appeler p95 DB une latence utilisateur.

## 3. Registre de parcours terrain : tous exigent une trace humaine

| ID | Geste / résultat observable terrain | Risque et preuve à conserver |
| --- | --- | --- |
| S01 | Dentiste ouvre l'Agenda, passe en Jour et consulte demain | Date et RDV du lendemain réellement visibles, clic et latence, pas de mutation |
| S02 | Recherche Benali avec homonymes | Choix explicite du dossier ; aucune sélection par défaut |
| S03 | Lecture patient autorisé | Identité + dossier tenant correctement affichés |
| S04 | Recherche « Mme Benali » | Désambiguïsation robuste et reprise après sélection |
| S05 | Secrétaire S05 propose RDV | Affichage **simulation / non exécutée**, aucun rendez-vous enregistré |
| S06 | Secrétaire S06 sans Agenda | 403 réel avant révélation du patient, aucune proposition exploitable |
| S07 | Deux créneaux adjacents, demandes concurrentes | Isoler les transactions ; observer absence de double réservation. **Hors action CB-01 en preview ; ne pas créer réellement de RDV avec Crown Bot** |
| S08 | Devis couronne côté dentiste | Brouillon `OPEN_DEVIS_EDITOR` non exécutable, pas de devis créé |
| S09 | Réservation ancienne (ABA) / modification concurrente | Contrôle CAS/idempotence par les gates spécialisés, puis scénario humain si une interface d'exécution autorisée existe ; **CB-01 preview ne possède pas cette action** |
| S10 | Secrétaire reçoit conflit 409 | Erreur explicite, état à revérifier, aucune confirmation fictive, pas d'action silencieuse |
| S11 | Recherche dossier tiers, inconnu et supprimé | Même 404, pas d'oracle d'identité multi-cabinets |
| S12 | GhostBrain « Marquer comme lu » | Alerte reste non lue si ACK refusé ; disparaît uniquement après succès confirmé |

Chaque ligne exige : rôle, tenant synthétique, exact SHA, viewport/zoom, étapes opérateur, résultat attendu/observé, fichier capture/trace, erreurs réseau, latence et delta DB. **NOT_RUN** ou **UNSUPPORTED** si indisponible ; ne jamais cocher PASS à partir d'un mock, d'un autre lot ou d'une simple capture.

## 4. Protocole révisé : FUE-C + revue transversale (18/10/2026)

**Correction du propriétaire pour cette mission CB-01** : le duo d'audit spécialisé « A sécurité/backend + B UX » n'est plus le protocole principal. L'épreuve est désormais **FUE-C (première valeur du module)** puis **revue transversale** des frontières UX→auth/poste→API/tenant→données→CI. Le laboratoire de référence est PR #783, source canonique `docs/audits/FIRST_USER_EXPERIENCE_PROMPT.md`. Ne jamais lancer les tests hors du sous-lot CB-01 ; PR #783 est une **source de méthode**, pas une autorisation de modifier son périmètre.

### Épreuve 1 — FUE-C adaptatif / utilisateur réel du module

Scénario : cabinet déjà configuré, dentiste ou secrétaire S05/S06 dans un poste autorisé, jeu de données fictif isolé. **First Value** définie avant test : consultation serveur effectivement utile (programme/patient autorisé) ou proposition S05 clairement **non exécutable**. L'affichage rapide des trois CTA **ne vaut pas First Value**. Contrôler session fraîche, trajet normal dans MainLayout/CrownBot, temps entrée→valeur, nombre de gestes/décisions, erreurs, reprise, S05 HTTP 200 `proposal_only`, S06 HTTP 403 sans divulgation, aucune écriture clinique. BEFORE/TARGET/AFTER 1280×900/1440×900/1600×900/1920×900, zoom **natif 200 % + NVDA dans la vraie application** ; 390/430 désignent le fallback **Web**, pas Pocket natif « En cours de construction ». Scorer sévèrement /10 chaque check, pondération FUE-C 20/20/15/25/20, ne pas inventer les temps ou résultats non exécutés.

### Épreuve 2 — revue transversale des frontières et de la vérité des preuves

Croiser SHA et artefacts, cookies/JWT/principal, Station 423, 403/404/409/422/503, droits et séparation tenant, homonymes, proposition sans UUID/action, absence de mutation, diff **complet** DB clinique synthétique, PostgreSQL HTTP vs primitives SQLCipher, concurrence CAS/ABA, GhostBrain WS et ACK, rendu UI/focus/zoom, 12 parcours humains, EXACT HEAD, CI REQUIRED/EXPERIMENTAL/HORS SCOPE et limites de la preuve. Scorer **chaque check** /10, retenir les dimensions critiques, chercher P0/BLOCKER/P1 MAJOR/P2 MINOR, faux green, fail-open et différences doc/code/tests. Un cas `NOT_RUN` reste `NOT_RUN`.

**Preuve d'exécution du protocole** : sur HEAD `9b021a0db1d12e1ac746a97d6c8eb7efa19b6544`, 17 contrôles indépendants de l'archive CI #12150517408 ont été exécutés hors navigateur : 14 PASS, 3 limitations NON VALIDÉES (temps entrée→First Value, diff DB clinique complet, parcours humains 0/12) ; SHA-256 `c47f8b592c9b604304c2ab11041577fc6c6eda1e078b7fbdf6276050b9aed5e0` vérifié. **Ce replay n'est ni un nouveau FUE utilisateur complet, ni une revue humaine indépendante.** Toute réexécution sur nouveau HEAD doit être traçable et ne doit pas transférer des preuves anciennes.

**Autorité restante** : `AGENTS.md` et `docs/quality/REALITY_PROOF_GATE.md` exigent actuellement toujours **deux perspectives adversariales distinctes**, revues et confirmation. Ici, FUE et transversal sont les **deux perspectives** ; une exécution par le même assistant demeure **interne** et n'autorise pas une note de revue indépendante ni `CONVERGED` à elle seule. Si la doctrine globale doit évoluer pour remplacer cette exigence, traiter ce changement sous une mission documentaire autorisée distincte, pas par suppression implicite d'un gate dans CB-01.

## 5. Décision / Next

Après FUE-C et revue transversale, rapprocher canonique, GitHub SHA, CI REQUIRED/EXPERIMENTAL/HORS SCOPE, roadmap et Notion POST. Un FIRST VALUE synthétique partiel n'est pas un succès humain : tant que les preuves RPG et les parcours terrain requis restent `NOT_RUN`, **CB-01 OPEN / NON CONVERGED**. Toute fusion/déploiement exige une **autorisation explicite distincte** ; aucun changement de flag de production.
