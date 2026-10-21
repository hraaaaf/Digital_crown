# Digital Crown — V1.5-06 / LOT06-P/P2-F01 — matrice de clôture partielle des preuves

Date : 2026-10-21. **STATUT : CHECKPOINT DOCUMENTAIRE LAB / LOT06 GLOBAL OUVERT / NO-GO SCM ET CLINIQUE.**
Ce document est une **classification de preuves**, ni un GO de merge, ni un assouplissement de gate, ni un changement de roadmap. Il n'autorise **aucune** installation/activation de service, accès cabinet/patient, essai matériel, migration, merge, déploiement ni création de nouvelles permissions.

## Source de vérité, HEAD et portée

- [PR parente #909](https://github.com/hraaaaf/Digital_crown/pull/909) : OPEN/DRAFT au HEAD vérifié `78c7983de911854ebddc7526d7461ee3a2e8a8df`, base `373ced67385a444996ba290755bdfcdd255440bf` (PR #901 OPEN/DRAFT et non mergée). #993 a été squash-merged **dans #909 seulement**, pas dans master.
- `master` au contrôle : `a2ad3002414a8a046221bb9993f71d0bfa8471a0`. Les preuves ci-dessous se rapportent au **HEAD #909**, jamais au master installable.
- **Canonique fonctionnelle V1.5-06 (page Notion)** : `Capture réelle → bon patient → serveur → dossier → audit → reprise après coupure sans doublon`. Le succès final **n'est pas observé**.
- [Roadmap V1.5 active](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb) : opérateur Imaging `DESKTOP_ONLY` ; logiciel/LAB au LOT06 ; essais de matériel physique au LOT10/10.4. [Plan FUE V1.5](https://app.notion.com/p/3f177c66336281c49a48d1361307f458) : FUE-G 06 terrain différé à LOT10.
- [LOT10 canonique](https://app.notion.com/p/3e677c66336281fcbe65f8889baf8c6a) : **exclusivement essais physiques**, et expressément **pas de développement produit**. Reporter le hardware au LOT10 ne reporte donc pas automatiquement une correction de sécurité produit au LOT10.
- [Runbook Codex Windows](./LOT06_P_CODEX_WINDOWS_ISOLATED_LAB_RUNBOOK.md) : `HOLD / REPORTÉ AU LOT10`, interdit l'accès PC/sandbox/installation durant LOT06-P ; l'[ADR P2](./LOT06_P_P2_WINDOWS_SCM_IDENTITY_WAL_MIGRATION_ADR.md) reste `DESIGN ONLY / HUMAN GATE REQUIRED`. Un HOLD sur les essais natifs **ne transforme pas les gates SCM en SKIPPED ou PASS**.

## Matrice décisionnelle — REQUIRED / EXPERIMENTAL / DIFFÉRÉ / HORS SCOPE

| Gate et résultat exigé | Nature | Statut probant au HEAD #909 | Preuve exacte / limite | Incidence closeout |
| --- | --- | --- | --- | --- |
| 06A hot-folder chiffré, quarantaine, dédup/replay et fail-closed sur données synthétiques | REQUIRED LAB | **GREEN — borné au LAB** | [06A #39502629817](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629817) SUCCESS ; Windows **435 tests : 434 PASS / 1 SKIP**, Ubuntu **435 : 405 PASS / 30 SKIP** ; test négatif de faux doublon #993 PASS sur les deux OS | Clore cette **preuve logicielle spécifique**, pas la fonction clinique |
| 06B préflight / intégration synthétique FastAPI et stabilité routes | REQUIRED LAB | **GREEN — software-only** | [06B #39502629433](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629433) SUCCESS, **27 tests** preflight/media + **6 tests** intégration synthétique ; 6 captures BEFORE/AFTER des **routes API**, non des écrans cliniques | Preuve de contrat/API partielle ; pas une attribution Patient/RDV validée |
| Périmètre de changements contrôlé, compatibilité de branche | REQUIRED | **GREEN sur SHA de #909** | [Scope #39502629779](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629779) SUCCESS ; [Portability #39502629544](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629544) SUCCESS | N'autorise ni merge master ni déploiement |
| ISO SID/DACL d'un **vrai** service Windows SCM en Session 0, refus effectif des écritures sur DB/WAL/SHM/keys et fiabilité/reprise SQLite | REQUIRED sécurité/fiabilité P2-F01 | **OPEN / NOT_TESTED SCM (W01–W12)** ; exécution **HOLD LOT10** | [ADR P2 §5](./LOT06_P_P2_WINDOWS_SCM_IDENTITY_WAL_MIGRATION_ADR.md) : 12 scénarios positifs/négatifs requièrent une VM NTFS jetable + GO distinct ; aucun jeton SCM réellement exercé pour ce service | **BLOCKER à la certification SCM et à la clôture produit** ; impossible de compter syntaxe/FUE user comme substitut |
| F01 deux utilisateurs Windows et restauration hostile en fixtures | EXPERIMENTAL | **GREEN laboratoire, pas SCM** | [FUE deux acteurs #39502629653](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629653) SUCCESS ; [Cross-SID ACL #39502629662](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629662) SUCCESS | Ne réduit pas les exigences W01–W12 |
| Source C# ServiceBase compilable / PowerShell valide sans exécution SCM | EXPERIMENTAL | **GREEN source/syntaxe uniquement** | [P2 syntax-only #39502629668](https://github.com/hraaaaf/Digital_crown/actions/runs/39502629668) SUCCESS ; compilation et parse, **pas** de StartService/StopService ni token effectif | Zéro certification native |
| Deux revues adversariales A/B **réellement indépendantes**, zéro BLOCKER/MAJOR sur **même HEAD final**, confirmation | REQUIRED de closeout critique | **OPEN / 0 sur 2 revues BLIND indépendantes démontrées** | [prompts A/B](./LOT06_P_P2_F01_BLIND_A_B_PROMPTS.md) ; revues internes présentes mais non indépendantes ; rapport Codex reçu = lecture documentaire seulement, `BLOCKED_BY_LOT10_HOLD` | Pas de `CONVERGED` ni score global de certification |
| Expérience opérateur/imaging réellement visible, association explicite Patient/RDV, serveur confirmant réception durable, audit, reprise bout en bout | REQUIRED si prétention fonctionnelle/clinique | **OPEN / aucun parcours clinique réel attesté** | Goal canonique LOT06 ; 06B préflight + fixtures ≠ ingestion authentifiée et affectation patient dans UI ; dépendances d'intégration au-delà du P2 lab | **LOT06 global reste ouvert** ; ne pas extrapoler les preuves LAB |
| Workflow « UI Human Visual Approval » | REQUIRED uniquement si surface produit concernée | **RUN GREEN mais preuve humaine NON APPLICABLE / NON FOURNIE** | [UI #39502625283](https://github.com/hraaaaf/Digital_crown/actions/runs/39502625283) : log `PASS trusted GitHub Action attestation: skipped-non-ui` ; aucune approbation réelle d'écran ni FUE staff | Ne pas cocher validation humaine du parcours opérateur |
| Acquisition réelle depuis matériel, test bout-en-bout vers patient fictif | REQUIRED au **LOT10/10.4** (terrain) | **DIFFÉRÉ officiellement / NOT_TESTED terrain** | Roadmap V1.5-10/10.4 et plan FUE canonique | Non exigé comme test physique pendant LOT06 ; **pas PASS**, ni excuse pour ignorer sécurité produit |
| Polissage Pocket/mobile de l'interface locale Imaging Desktop | HORS SCOPE UX (sauf surface partagée réellement exposée) | **NOT_APPLICABLE** | Décision Desktop-only 2026-10-16 ; photo Wi-Fi depuis téléphone ≠ UI Pocket | Ne pas ouvrir de chantier mobile cosmétique par défaut |
| GitHub PR #909 vers master, packaging, activation clinique | GATE irréversible / owner | **NO-GO / NON AUTORISÉ** | #909 OPEN/DRAFT ; master non changé | Ne pas fusionner, installer, exporter de secrets, ni activer |

## Décision et séquence exacte

1. **CHECKPOINT LAB PARTIEL VALIDÉ :** tests de code 06A/06B, scope et expériences explicitement étiquetés ci-dessus ont des preuves exact HEAD ; ne pas rejouer aveuglément les mêmes CI sans changement pertinent.
2. **PAS DE CLOSEOUT TOTAL :** le résultat final fonctionnel Patient/RDV/serveur/audit n'est pas attesté ; F01 SCM W01–W12 est obligatoire et non testé ; revues BLIND 0/2 ; #909 en DRAFT. **Aucun score global /10 de certification**.
3. **HOLD conservé :** ni Codex Windows, ni service SCM, ni sandbox PC du propriétaire durant LOT06-P en vertu du runbook. Si la roadmap souhaite déplacer des **essais natifs non matériels** au LOT10, il faut une **décision canonique explicite** ; LOT10 ne doit pas devenir implicitement un chantier de développement.
4. **Next autorisé au sein de LOT06 :** documenter/sécuriser seulement les contrats LAB encore insuffisants, organiser les deux vrais avis A/B si moyens autorisés ; sinon noter la dépendance et rester OPEN. Le test réel SCM requiert d'abord la levée du HOLD + protocole/gate VM séparé, et **GO SCM privilégié distinct**.
5. **Décision de merge :** non prise. PR documentaire empilée sur #909 restera DRAFT ; un éventuel merge de cette PR documentaire ne doit pas être confondu avec fusion de #909/master. Les règles REQUIRED/EXPERIMENTAL/HORS SCOPE continuent à s'appliquer.

## Réserves (non supprimées)

- La preuve Windows native implique des droits SCM et la mesure de **DACL effective/OWNER RIGHTS**, puis COMMIT/WAL/crash/backup/restore ; une compilation verte ou deux comptes standard ne suffit pas.
- La première entrée spool testée au démarrage n'est pas un **scrub complet** ; `.ready` replay rapide ne réauthentifie pas tous les octets à chaque poll ; `read_verified` est requis avant usage.
- Le **report spécifique du runbook au LOT10** et le mandat **LOT10 physique-only** sont une tension de séquencement à arbitrer explicitement, **pas** une levée de sécurité. Voir `techdoubt.md`.
- Aucune validation indépendante externe prétendue. Reprise de vérification au nouveau HEAD si un code/harness change.

**Verdict final :** `LOT06-P/P2-F01 — LAB EVIDENCE CHECKPOINT COMPLETE / SCM F01 OPEN / #909 DRAFT / LOT06 PRODUCT NO-GO`.
