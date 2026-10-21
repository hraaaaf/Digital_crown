# Digital Crown — CB-01 FIRST_VALUE_UI — matrice FUE-first S01–S12 et contrôles transversaux

**Date :** 2026-10-17. **Statut :** guide d'exécution, pas certificat terrain ni permission de déployer.  
**PR cible :** [#904](https://github.com/hraaaaf/Digital_crown/pull/904) (draft, base #903).  
**Scope :** Crown Bot Cabinet Web Desktop uniquement ; Pocket « En cours de construction ». Aucun patient réel, action clinique, activation de flag prod, fusion ou déploiement autorisés par ce guide.

## Addendum de gouvernance FUE-first — 21 octobre 2026 (CB-01 seulement)

L'ancienne version de ce runbook imposait systématiquement 12 attestations humaines et deux reviewers indépendants pour CONVERGED. Cette condition était liée à la doctrine de l'ancien `AGENTS.md`. La politique en vigueur sur `master` au 21/10/2026 — `AGENTS.md`, `.claude/rules/execution-scoring-verification.md`, `docs/quality/REALITY_PROOF_GATE.md` et `.claude/rules/visual-closeout-human-validation.md` — est **FUE-first**. Pour le closeout **logiciel isolé CB-01**, aucun quota fixe de reviewers externes ni douze opérateurs physiques n'est imposé par défaut. Une validation humaine/clinique/visuelle/physique **expressément requise** reste un gate distinct et ne peut jamais être simulée.

**But effectivement livré :** Cabinet Web Desktop, accès authentifié, consultation serveur et **proposition RDV non exécutable** ; S07/S09 (exécution transactionnelle) sont UNSUPPORTED en preview, Pocket native « En cours de construction », RPG-P réel réservé au Lot 10. La matrice S01–S12 est un **registre de couverture et de cas négatifs**, pas un décompte automatiquement bloquant `0/12 humains`.

**Parcours FUE cible :** profil navigateur vierge → véritable login **dans l'UI** du produit test isolé (pas une session injectée par API) → MainLayout réel → Crown Bot → première donnée serveur utile ou proposition S05 affichée `proposal_only` → refus S06 `403` sans fuite → persistance clinique non modifiée. Sans la preuve du login UI, la FUE-G intégrée n'est **pas** entièrement démontrée. Les trois CTA ne constituent jamais la First Value. Le résultat utile non exécutable est le plafond fonctionnel légitime du preview, pas un échec faute de booking.

**Scoring :** sur le HEAD candidat de clôture ou gate critique, `EXECUTION_SCORE` et `FUE_EVIDENCE_SCORE` séparés ; `RETAINED_SCORE=min(...)`. L'ancien `ADVERSARIAL_SCORE` n'est qu'un champ historique/de compatibilité. Les deux angles **internes** FUE produit et contrôles transversaux sont conservés pour ce lot significatif ; aucune fausse revue externe. Tests ciblés et confirmation du HEAD final, pas de rerun global automatique. Le 7,4/10 précédent n'est pas transférable sous un autre nom.

## 1. Deux types de preuve qui ne se remplacent pas

La CI Ubuntu + Chromium exécute, sur base SQLite jetable isolée, les contrats HTTP S02/S03/S04/S05/S06/S08/S11 et le parcours navigateur S01 **Agenda → Jour → lendemain**. Le fichier d'artefact `s01-s12-synthetic-matrix.json` fait foi seulement pour le SHA contenu dans `exactHead`. Les tests S07/S09/S10/S12 pouvant apparaître dans d'autres gates (concurrence, Vitest) **ne deviennent pas automatiquement des parcours UI humains CB-01 PASS**.

Le contrôle **physique** par un opérateur sur **DESKTOP-3MAJEEH**, lorsqu'il est explicitement demandé et autorisé, nécessite ce poste isolé, autorisé et des données entièrement fictives ; il ne devient pas un prérequis par défaut du merge logiciel CB-01. Le poste était OFFLINE au contrôle historique cité. Aucune synchronisation des données d'un cabinet réel ; jamais installer un HEAD de PR non `INSTALLABLE_CERTIFIED` sur un vrai cabinet.

### Alternative GitHub Actions si DESKTOP-3MAJEEH est hors ligne

La [CI expérimentale CB-01](https://github.com/hraaaaf/Digital_crown/actions/workflows/cb01-associate-sidecar-visual.yml) exécute un job **Ubuntu/Chromium synthétique** avec fausses identités et fixtures jetables, ainsi qu'un job **Windows hébergé GitHub**. Ce job Windows Sidecar exécute Vitest JSDOM et conserve des attestations (69/69 tests au SHA `e1afb65`). **Un autre job Windows FUE-G**, [#39471983766](https://github.com/hraaaaf/Digital_crown/actions/runs/39471983766), a réellement exécuté un Chromium graphique + FastAPI/SQLCipher fictif, le zoom natif Chrome `1→2` et NVDA (59 phrases, cinq contrôles rôle+nom), ainsi que S05 `200 proposal_only` / S06 `403`. Les deux restent **automatisés, zéro utilisateur humain** ; ni connexion initiale via vrai login UI ni installation cabinet réelle attestées. Ne pas rétrograder ces preuves réelles au simple JSDOM, ni leur attribuer une couverture qu'elles n'ont pas.

**Règle de preuve :** un runner Windows ne représente pas un cabinet physique ; JSDOM n'est pas un navigateur complet, mais le banc Windows FUE-G dispose bien d'une **preuve de zoom natif et d'annonces NVDA automatisées**. Les captures Chromium six viewports sont synthétiques, peuvent étayer l'accord propriétaire sur les images, mais ne prouvent ni login UI vierge, ni opérateur indépendant. **Aucune obligation de deux reviewers externes par défaut** ; les approbations humaines explicitement requises, et les contrôles de sécurité/permissions/données propres au risque, restent obligatoires. Ne pas activer Pocket, flag de prod, merge ni déploiement par cette preuve.

## 2. Préalables fail-closed

1. Lire HEAD exact de #904 et de ses bases et vérifier le SHA **du code réellement testé** ; si une session T2 physique est explicitement approuvée, contrôler la provenance du bundle installable séparément. Un commit documentaire invalide l'identité strictement exacte des anciennes attestations ; conserver les SHA anciens et revérifier les gates **impactés**, sans faux transfert de ZIP.
2. Pour chaque FUE logicielle exécutée : backend/frontend réels isolés, comptes/tenants/patients fictifs, localhost et credentials protégés ; vérifier opt-in du poste synthétique, droits et refus 423 sans contourner l'enrôlement. **Entrer par le vrai formulaire login UI et un profil vierge** pour qualifier la FUE-G. Un essai T2 physique reste un gate distinct seulement s'il est réellement autorisé.
3. Snapshot base **complète** et audit : tables, nombre de rendez-vous, BotPendingAction, patients, devis, échantillons, alertes ; distinguer les écritures techniques attendues (auth/workstation) des écritures cliniques interdites. Conserver rapport diff après exécution.
4. BEFORE / Target / AFTER aux viewports **1280×900, 1440×900, 1600×900, 1920×900** pertinents, même profil/état/rôle ; 390/430 sont du **Web fallback**, pas Pocket native. Préserver la preuve Windows zoom **natif 200 %** + NVDA automatisée ; demander une observation humaine sur le HEAD visuel final lorsque le gate de validation des captures l'exige. Une largeur CSS réduite seule n'est pas un zoom natif.
5. Mesurer entrée → DOM réellement utile, clics/décisions, HTTP distinct et reprises dans la FUE. Une campagne de **30 lectures et p50/p95** est requise **pour soutenir une revendication de performance humaine/p95** ; tant qu'elle n'est pas exécutée, noter `NOT_RUN_METRIC`, sans inventer une latence d'utilisateur ni transformer mécaniquement ce protocole de recherche en gate global du preview.

## 3. Registre de couverture S01–S12 — preuve applicable, pas quota humain universel

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

Pour tout scénario **réellement exécuté**, consigner : rôle, tenant fictif, SHA exact, viewport/zoom, étapes de l'opérateur **ou de l'automate**, attendu/observé, réponse HTTP, trace/capture, erreurs réseau, latence et delta DB appropriés ; indiquer la nature `AUTO_BROWSER`, `AUTO_HTTP`, `HUMAN`, `TECHNICAL_PRIMITIVE`. **NOT_RUN** ou **UNSUPPORTED** si indisponible. Un mock, un runner ou une capture ne devient jamais un PASS humain. S07/S09 UNSUPPORTED en preview, ne pas exécuter de booking réel.

## 4. Protocole révisé : FUE-C + revue transversale (18/10/2026)

**Correction du propriétaire pour cette mission CB-01** : le duo d'audit spécialisé « A sécurité/backend + B UX » n'est plus le protocole principal. L'épreuve est désormais **FUE-C (première valeur du module)** puis **revue transversale** des frontières UX→auth/poste→API/tenant→données→CI. Le laboratoire de référence est PR #783, source canonique `docs/audits/FIRST_USER_EXPERIENCE_PROMPT.md`. Ne jamais lancer les tests hors du sous-lot CB-01 ; PR #783 est une **source de méthode**, pas une autorisation de modifier son périmètre.

### Épreuve 1 — FUE-C / parcours réel dans l'application de test isolée

Scénario : cabinet de test configuré, dentiste ou secrétaire S05/S06 sur poste de test autorisé, tenants et données fictifs. Commencer, lorsque pertinent, par **vrai login UI sur session vierge**, puis MainLayout/CrownBot. **First Value** : consultation serveur effectivement utile (programme/patient autorisé) ou proposition S05 clairement **non exécutable** ; trois CTA seuls ne valent rien. Vérifier S05 HTTP 200 `proposal_only`, S06 HTTP 403 sans divulgation, aucune écriture clinique, erreurs/reprise, gestes/décisions, chrono DOM utile, BEFORE/TARGET/AFTER aux 4 largeurs desktop, plus vrai zoom Chromium 200%/NVDA quand le risque l'exige. 390/430 restent Web fallback, pas Pocket native. Évaluer chaque dimension FUE-C /10, pondération descriptive 20/20/15/25/20 ; cette pondération ne remplace pas `FUE_EVIDENCE_SCORE` ni les gates binaires. Une FUE automatisée **réellement exécutée** est recevable comme preuve intégrée, mais ne se présente pas comme une session humaine.

### Épreuve 2 — revue transversale des frontières et de la vérité des preuves

Croiser SHA et artefacts, cookies/JWT/principal, Station 423, 403/404/409/422/503, droits et séparation tenant, homonymes, proposition sans UUID/action, absence de mutation, diff **complet** DB clinique synthétique, PostgreSQL HTTP vs primitives SQLCipher, concurrence CAS/ABA, GhostBrain WS et ACK, rendu UI/focus/zoom, matrice S01–S12 selon preuves auto/humaines applicables, EXACT HEAD, CI REQUIRED/EXPERIMENTAL/HORS SCOPE et limites de la preuve. Scorer **chaque check** /10, retenir les dimensions critiques, chercher P0/BLOCKER/P1 MAJOR/P2 MINOR, faux green, fail-open et différences doc/code/tests. Un cas `NOT_RUN` reste `NOT_RUN`.

**Preuve d'exécution du protocole** : sur HEAD `9b021a0db1d12e1ac746a97d6c8eb7efa19b6544`, 17 contrôles indépendants de l'archive CI #12150517408 ont été exécutés hors navigateur : 14 PASS, 3 limitations NON VALIDÉES (temps entrée→First Value, diff DB clinique complet, parcours humains 0/12) ; SHA-256 `c47f8b592c9b604304c2ab11041577fc6c6eda1e078b7fbdf6276050b9aed5e0` vérifié. **Ce replay n'est ni un nouveau FUE utilisateur complet, ni une revue humaine indépendante.** Toute réexécution sur nouveau HEAD doit être traçable et ne doit pas transférer des preuves anciennes.

**Autorité actuelle (21/10)** : les documents FUE-first alignés sur `master` n'exigent **ni deux reviewers externes ni douze parcours humains par défaut**. Ce lot significatif conserve deux **perspectives critiques internes** (vérité FUE, sécurité/transversal) et une confirmation finale sur le même HEAD, sans les appeler reviewers indépendants. La décision CONVERGED dépend des résultats réellement exécutés, du score >=9, des gates REQUIRED et des éventuelles approbations humaines **explicitement applicables**. Le texte précédent de ce runbook est remplacé sur ce point ; les règles patient/privacy/no-write ne sont pas assouplies.

## 5. Matrice de gates FUE-first CB-01 (logiciel uniquement)

| Gate | Classe | Preuve au SHA produit `e1afb65…` (20/10) | Décision / reste |
| --- | --- | --- | --- |
| FUE-I / RPG-J première valeur visible réellement utile via MainLayout + FastAPI fictif | **REQUIRED** | [Windows FUE-G #39471983766](https://github.com/hraaaaf/Digital_crown/actions/runs/39471983766) : S05 200 `proposal_only` visible, S06 403 ; [Sidecar #39471983966](https://github.com/hraaaaf/Digital_crown/actions/runs/39471983966) ; 8 clics / 6 réponses saisies | **PARTIEL** : trajet authentifié, mais **vrai login UI depuis profil neuf non exécuté** ; FUE-G intégrée non certifiée |
| RPG-C/F négatifs RBAC / tenant / station 423 / S06 refus / 404 homonymes / aucun booking exécutable | **REQUIRED** | API et navigateur isolés + 119 tables SQLCipher **état final** sans mutation clinique ; traces distinctes dont S05/S06 | **PASS technique partiel** ; écritures cliniques transitoires non exclues par seul snapshot final, confidentialité et tests négatifs toujours exigibles |
| BEFORE → Target → AFTER mêmes viewports, responsive Web et accord humain sur rendu final | **REQUIRED (UI)** | Six largeurs synthétiques 390/430/1280/1440/1600/1920, captures comparables et approbations propriétaire A–F + 1280/1600 sur ancien SHA produit ; [Sidecar #39471983966](https://github.com/hraaaaf/Digital_crown/actions/runs/39471983966) | **PASS partiel** pour le rendu approuvé et code inchangé ; ne pas inventer Pocket native ni consentement sur nouveau rendu |
| NVDA 5 contrôles + zoom Chromium natif 200% sur vrai navigateur Windows | **EXPERIMENTAL — preuve utile de risque UI** | [Windows #39471983766](https://github.com/hraaaaf/Digital_crown/actions/runs/39471983766) : 59 annonces, 5/5, zoom 1→2 | **PASS laboratoire**, pas WCAG complète ni session humaine |
| Contrôles transversaux supplémentaires lorsque risque patient/RBAC le justifie | **REQUIRED SI APPLICABLE** | S10/S12 tests ciblés spécialisés ; S07/S09 primitives de concurrence, pas action du bot | Conserver oracles et résultats sans promotion en E2E |
| Campagne 30 lectures humaines + p50/p95 ; 12 attestations humaines ; deux reviewers externes | **CONDITIONNEL / NON REQUIRED PAR DÉFAUT** | 0/12 attestations humaines ; 0/2 reviewers externes | N'empêche pas seul un closeout logiciel FUE-first ; ne revendiquer ni p50/p95 ni validation humaine réellement absente |
| S07/S09 création effective de RDV en preview ; Pocket native ; RPG-P matériel Lot 10 | **HORS SCOPE / DIFFÉRÉ** | Interface d'exécution absente ; Web mobile fallback seulement | `UNSUPPORTED` / différé ; jamais FAIL du gate logiciel CB-01 |

**Scoring indicatif de requalification (sur preuves du SHA produit, non un nouveau PASS) :** `EXECUTION_SCORE=7.6/10`, `FUE_EVIDENCE_SCORE=7.2/10`, `RETAINED_SCORE=7.2/10`, écart `0.4`, plafond preuve/gate requis incomplet `<=7.9`. Justification FUE : vrai backend/UI/S05/S06/zoom NVDA, mais pas de **login UI frais** documenté, seulement un parcours automatisé S05, friction 8 clics/6 réponses et pas de preuve d'absence d'écritures transitoires. Ceci n'est pas un score final certifiant le nouveau HEAD documentaire : aucune nouvelle exécution du parcours utilisateur après changement doc ne peut être inventée. L'ancien 7,4/10 ADVERSARIAL reste **historique**.

**Décision :** CB-01 logiciel **OPEN / VERIFIED=NON / CONVERGED=NON** sur FUE intégrée, mais **0/2 reviewers externes n'est plus un gate automatique**. Utiliser le FUE réel sur navigateur et backend isolés (depuis login UI), captures, sécurité/tenant et confirmation des seules preuves impactées ; sur changement documentaire seul, ne pas invalider fonctionnellement les tests code inchangé, mais toujours attribuer chaque artefact à son SHA réel. Reporter les limites dans `docs/crown-bot/techdoubt.md`. **CB-02 gelé ; Lot 10 physique différé ; aucun merge, flag, installation ni déploiement autorisés sans GO distinct.**
