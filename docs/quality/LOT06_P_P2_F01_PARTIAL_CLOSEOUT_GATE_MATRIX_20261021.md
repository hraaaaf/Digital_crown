# LOT06-P / P2-F01 — matrice de clôture partielle et de non-convergence (2026-10-21)

**Statut : CHECKPOINT DOCUMENTAIRE / LOGICIEL LAB VERT / P2-F01 OPEN / NO-GO SCM ET CLINIQUE.**  
**Autorité :** registre d'observation, **non** amendement de roadmap, non levée de HOLD, non closeout LOT06 et non approbation de merge.

## Mission et référence immuable

- Repo : `hraaaaf/Digital_crown` ; [PR parent #909](https://github.com/hraaaaf/Digital_crown/pull/909) **OPEN/DRAFT**, HEAD de preuve **`78c7983de911854ebddc7526d7461ee3a2e8a8df`**, base de PR **`373ced67385a444996ba290755bdfcdd255440bf`**.
- [PR #993](https://github.com/hraaaaf/Digital_crown/pull/993) : **MERGED dans la branche #909 seulement**, commit `78c7983de911854ebddc7526d7461ee3a2e8a8df`; `master` au contrôle : `a2ad3002414a8a046221bb9993f71d0bfa8471a0`. [PR #901](https://github.com/hraaaaf/Digital_crown/pull/901) sous-jacente également OPEN/DRAFT. Les états sont des instantanés, à revalider avant toute décision.
- Lot : **V1.5-06 Imaging Acquisition Gateway** ; chantier limité ici : **LOT06-P / P2-F01**. Aucun travail LOT05, LOT07, LOT10 ou sur station clinique autorisé par ce registre.
- Sources prioritaires : [roadmap V1.5 canonique](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb), [page LOT06](https://app.notion.com/p/3e677c66336281639beae2a946df1483), [FUE par lot](https://app.notion.com/p/3f177c66336281c49a48d1361307f458), [LOT10 physique](https://app.notion.com/p/3e677c66336281fcbe65f8889baf8c6a), [ADR P2 SCM](LOT06_P_P2_WINDOWS_SCM_IDENTITY_WAL_MIGRATION_ADR.md), [runbook Codex Windows](LOT06_P_CODEX_WINDOWS_ISOLATED_LAB_RUNBOOK.md), [prompts A/B](LOT06_P_P2_F01_BLIND_A_B_PROMPTS.md) et `techdoubt.md`.
- Objectif V1.5-06 **non atteint au niveau produit** : capture réelle → patient exact → serveur → dossier → audit → reprise après coupure sans doublon. Les tests LAB ne fournissent pas cette chaîne clinique.

## Statuts sémantiques, à ne pas confondre

- **PASS LAB** : preuve positive ou négative exécutée sur fixtures synthétiques et SHA identifié, dans les limites décrites.
- **OPEN / BLOCKER** : une obligation du lot ou de P2-F01 manque ; interdit `VERIFIED`, `CONVERGED`, activation/merge produit.
- **NOT_TESTED** : aucune exécution du scénario natif concerné, même si source et syntaxe passent.
- **DEFERRED LOT10 — EXPLICITE** : seulement ce que la roadmap/FUE et le runbook ont effectivement reporté ; ce label ne convertit **aucun** gate sécurité P2 requis en PASS.
- **HORS SCOPE DU CHECKPOINT** : périmètre non modifié par cette note, sans désactiver son gate dans les lots parents.
- **REQUIRED / EXPERIMENTAL / HORS SCOPE** : classe de vérification relative au sous-lot ; un workflow expérimental réussi n'est jamais substituable à un gate REQUIRED.

## Matrice de décision — preuve / frontière / Next

| Gate / périmètre | Classe | État au HEAD parent | Preuve exacte et limite | Next avant clôture |
|---|---|---|---|---|
| Scope LAB, absence de code produit dans le correctif #993 | REQUIRED documentaire | **PASS** | Fusion #993 : exactement `gateway.py`, `test_gateway.py`, `techdoubt.md` ; [Scope parent #39502629779](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629779) SUCCESS | Garder #909 DRAFT ; ne pas extrapoler au diff historique de 39 fichiers de #909 |
| Hot-folder synthétique, clé/spool, redémarrage, refus blob `.ready` forgé | REQUIRED LAB | **PASS LAB** | [06A #39502629817](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629817), checkout exact SHA ; Windows 435 tests, **434 PASS/1 SKIP** ; Ubuntu 435 tests, **405 PASS/30 SKIP** ; `test_ready_mode_tampered_ledger_blob_cannot_fake_duplicate` PASS sur les deux OS | Conserver la preuve, pas de rerun sans impact ; déduplication rapide ne déchiffre pas chaque poll, `read_verified` est séparé |
| Préflight logiciel, Media Core, vrai lifespan FastAPI en environnement synthétique | REQUIRED LAB | **PASS LAB** | [06B #39502629433](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629433) : 27 tests de préflight/media et 6 tests lifespan LAB PASS ; 6 captures de **routes FastAPI**, non de parcours clinique | Ne pas étiqueter comme patient lié, installateur, interface utilisateur ou production |
| Portabilité, contrôle de fichiers/permissions de deux comptes standards | REQUIRED/EXPERIMENTAL selon gate | **PASS sur leur contrat LAB** | [Portability #39502629544](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629544), [Cross-SID F01 #39502629662](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629662), [FUE A+B deux acteurs techniques #39502629653](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629653) SUCCESS. Deux comptes standards ≠ véritable principal SCM | Ne pas convertir en isolement effectif du service Windows |
| Fixture native SCM (code C# / PowerShell) | EXPERIMENTAL source-only | **PASS SYNTAXE / SCM NOT_TESTED** | [Syntax #39502629668](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629668) compile C# et parse PS, **sans exécuter/installer de ServiceBase** | Exiger vraie identité, Session 0 et tests natifs distincts lorsqu'ils seront légalement autorisés |
| Service Windows SCM réel : token, Service SID, Session 0, service object DACL, sidecars DB/WAL/SHM, fail-close et recovery (ADR **W01–W12**) | **REQUIRED pour certification P2-F01** | **BLOCKED / NOT_TESTED**, 12/12 | ADR P2 section 5 : chaque W01–W12 = NOT TESTED ; seul labo synthétique existant. [Runbook Codex](LOT06_P_CODEX_WINDOWS_ISOLATED_LAB_RUNBOOK.md) débute par **HOLD / REPORTÉ AU LOT10 (décision 2026-10-17)**, interdit Codex/PC/sandbox durant LOT06-P et interdit service/admin dans son mode TEMP. Rapport Codex transmis par le propriétaire : `BLOCKED_BY_LOT10_HOLD`, aucun test Windows | **Arbitrage canonique humain nécessaire** pour articulation entre gate REQUIRED P2 et HOLD PC LOT10 ; pas d'exécution SCM/VM privilégiée sans nouveau mandat explicite, et pas de certification pendant ce HOLD |
| FUE-G 06 : acquisition sur **matériel réel** jusqu'au bon dossier patient | REQUIRED **au LOT10**, **hors périmètre physique LOT06** | **DEFERRED LOT10/10.4 EXPLICITE, NOT_TESTED terrain** | [FUE V1.5-06](https://app.notion.com/p/3f177c66336281c49a48d1361307f458) et [LOT10/10.4](https://app.notion.com/p/3e677c66336281fcbe65f8889baf8c6a). **C'est le FUE physique qui est reporté**, pas la réussite du produit ni tous les tests sécurité P2 | À exécuter seulement dans la séquence LOT10 avec données/personas synthétiques et gate préalable GLOBAL-G10-S |
| FUE installateur, staff/patient association, erreurs/retry, autorisation serveur/receipt et interface opérateur | REQUIRED lorsque parcours réellement présent | **OPEN / non prouvé de bout en bout** | FUE par lot spécifie `FUE-I` installateur/staff/recovery, et intégration patient; `06B` n'est qu'une route/fixture. Opérateur **DESKTOP_ONLY** selon décision canonique 2026-10-16 ; la source photo smartphone ne crée pas une UI Pocket | Exécuter seulement les parcours logiciels rendus utilisables ; ne pas inventer un FUE UI, vérifier tenant/autorisation/attribution explicite/receipt avant claim |
| Review A et B réellement indépendantes, puis confirmation même HEAD | REQUIRED pour `CONVERGED` | **OPEN / 0/2 propre au HEAD final** | [Prompts blind A/B](LOT06_P_P2_F01_BLIND_A_B_PROMPTS.md), anciens rapports à SHA antérieurs, perspectives internes ≠ deux reviewers blind ; Codex bloqué n'est pas une revue native | Deux contextes d'audit séparés, sans contamination, et 0 BLOCKER/MAJOR sur SHA final ; nouvelles revues après chaque nouveau code HEAD |
| UI Human Visual Approval | conditionnel UI effective | **CI TECHNIQUE SUCCESS, approbation utilisateur NON PROUVÉE** | [run #39502625283](https://github.com/hraaaaf/Digital_crown/actions/runs/39502625283) : `PASS trusted GitHub Action attestation: skipped-non-ui`. Ce n'est pas un BEFORE/AFTER d'UI humaine ni un GO personnel | Ré-évaluer si route/interface opérateur réellement impactée, pas de fausse validation |
| PR #909 → base #901 → master, installable et cabinet | **HUMAN / RELEASE GATES** | **NO-GO / NON FUSIONNÉ** | #909 et #901 DRAFT, pas de certificat `INSTALLABLE_CERTIFIED`, pas de tests SCM ni réception clinique réels | Pas de ready/merge/master, migration, appareil, clé réelle ou Vercel au titre de ce document |

### W01–W12 — disposition explicite unique

| W01–W04 | W05–W08 | W09–W12 |
|---|---|---|
| **BLOCKED_BY_LOT10_HOLD / NOT_TESTED SCM** | **BLOCKED_BY_LOT10_HOLD / NOT_TESTED SCM** | **BLOCKED_BY_LOT10_HOLD / NOT_TESTED SCM** |

Cette ligne groupe les statuts, pas les scénarios : **W01, W02, W03, W04, W05, W06, W07, W08, W09, W10, W11, W12** sont chacun **NOT_TESTED sous vrai SCM**, conformément à l'ADR P2. Les succès de sous-tests SQLite/ACL synthétiques ne ferment aucun Wxx.

## Décision documentaire, sans révision de roadmap

1. **ACQUIS / conserver** : preuve purement logicielle LAB sur `78c7983de911854ebddc7526d7461ee3a2e8a8df`, 12/12 workflows observés terminés : **11 SUCCESS, 1 SKIPPED** M6-I hors scope, zéro échec ; ne pas relancer volontairement la CI sans changement impactant.
2. **NON ACQUIS** : P2-F01 SCM réel, séparation effective identité/NTFS, durabilité et restore natifs, vraie application UI autorisée et indépendante, deux audits blind frais. **`LOT06-P/P2-F01 = OPEN / NOT CONVERGED / NO-GO`.**
3. **REPORT EXPLICITE** : FUE-G terrain imagerie **LOT10.4**, plus runbook d'accès au PC/VM réservé LOT10. Ce report **ne constitue pas une résolution** de l'obligation ADR W01–W12 nécessaire à la certification P2.
4. **RÉSERVE DE GOUVERNANCE BLOCKER** : décider formellement, dans la roadmap canonique après consultation propriétaire, soit (a) un gate natif P2 exécuté dans un environnement LAB approuvé et exempté explicitement du HOLD, soit (b) une réduction/requalification formelle de la portée P2 avec dépendance produit maintenue jusqu'au LOT10 ; **aucune de ces branches n'est autorisée ici**. Si l'on garde les gates inchangés, #909 reste DRAFT et P2 non clos. Une clôture partielle LAB n'ouvre pas LOT07 ni une sortie de LOT06.
5. **Next exact sans tokens gaspillés** : archiver cette matrice + `techdoubt.md` comme **handover DRAFT empilé sur #909** ; vérifier diff/docs uniquement, signaler tout CI documentaire déclenché sans l'extrapoler ; prochain GO nécessaire uniquement pour arbitrage sur séquencement ou opération SCM privilégiée, pas pour relecture documentaire. Prochain lot non démarré.

## Revue adversariale interne du document (pas independent BLIND)

- **A — sécurité** : risque de faux vert si l'on transforme F01 cross-SID standard en preuve de Service SID/OWNER RIGHTS, si l'on exécute Codex malgré le HOLD, ou si un `skip-non-ui` est lu comme approbation. Statuts sûrs maintenus : BLOCKED / NOT_TESTED / NO-GO.
- **B — fiabilité/gouvernance** : risque de faux closeout si l'on reporte W01–W12 simplement parce que FUE-G physique est au LOT10 ; séquence et autorisations sont séparées. L'inventaire d'essais ne prouve pas l'absence de régression du vrai SCM ni un chemin backup/restore clinique.
- **Score de l'étape documentaire (provisoire, borné par validation de diff)** : EXECUTION 7.9/10, ADVERSARIAL 7.9/10, RETAINED 7.9/10, écart 0. **Pas `VERIFIED`** ; aucun test runtime nouveau, pas de revue indépendante ni d'aval de release. **Score clinique/SCM : BLOCKED, max 5.9/10** par les preuves sécurité/recovery obligatoires absentes.

## Note de non-effacement

Les résultats des runs antérieurs restent vrais pour leur **SHA d'exécution**, pas automatiquement pour un nouveau HEAD ; le correctif ajouté ici est **documentation-only** (et réserve), aucune prétention de recertification logicielle. Le merge de #993 dans #909 est acquis ; aucune décision implicite sur les autres 39 fichiers de la PR par cette matrice.
