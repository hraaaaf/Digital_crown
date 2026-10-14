# Digital Crown — LOT04 × Pocket — registre des PR résiduelles (14 octobre 2026)

> **STATUT : DOCUMENT DE TRAÇABILITÉ, CANDIDAT DOCS-ONLY ; NON CERTIFICATION CLINIQUE OU MOBILE.**
> Contexte : le propriétaire a autorisé la fusion logicielle [#882](https://github.com/hraaaaf/Digital_crown/pull/882) puis le nettoyage des anciennes PR.
> **État produit vérifié** : `master@55b1985fefbd6d3522813d123985ea3f094d9012`, #882 MERGED. Le [run PostgreSQL post-merge #38548499537](https://github.com/hraaaaf/Digital_crown/actions/runs/38548499537) est SUCCESS sur ce SHA (PostgreSQL 18 + Windows PowerShell 5.1) ; ce run n'est **pas** la certification intégrale du cabinet.
> Autorité de pilotage : [roadmap unique V1.5 Notion](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb) et [handover LOT04 × Pocket](https://app.notion.com/p/3f977c66336281a59413ef90d9a28d65). Cette pièce n'ouvre aucun nouveau lot et ne remplace aucun gate.

## 1. Décisions utiles conservées, sans transformer les anciennes PR en nouvelles fonctionnalités

### #848 — Politique 04.8, choix propriétaire **C** (Station et accueil selon configuration)

La [spécification historique intégrale de #848](https://github.com/hraaaaf/Digital_crown/blob/7b94f8ad9a8bcef830164464a79f35491ea7fbad/docs/quality/V15_04_8_SECURE_STATION_PRINTING_DESIGN.md) reste la provenance de la décision propriétaire du 12 octobre 2026. La conception distingue `disabled` (défaut), `near_station`, `reception`, `both`. Elle propose de réutiliser la confirmation Desktop `StudioFooter` et de n'utiliser le mécanisme de navigateur Desktop que sur un poste staff de confiance, après revalidation de l'archive finale.

**Invariants qui restent impératifs** : aucune récupération de PDF par le navigateur Station (HTTP 423), aucune autorisation par simple QR/session, réexamen du tenant/patient/empreinte/autorisation de praticien, allowlist de destination, déduplication atomique entre deux destinations, état `uncertain` sans réimpression automatique, remise protégée physiquement, aucun secret de déblocage sur écran public, aucune affirmation « imprimé » sur seul acquittement spool.

**Attention chronologique** : les passages du document #848 disant « non implémenté » décrivent la **photographie du 12 octobre**, avant l'intégration logicielle #882 du 14 octobre. Des garde-fous B/C/D et une UI désactivée existent désormais en logiciel ; la certification de l'imprimante physique, le vrai routage vers deux destinations et la libération réelle restent **OUVERTS / LOT10**. Le choix C n'autorise pas l'activation automatique.

### #836 — Risques documentaires historiques de la feuille de soins 04.3

L'[audit de reprise de #836](https://github.com/hraaaaf/Digital_crown/blob/5dfad4dc52b1aec96dc19eef0dd38b5a8bc7e179/docs/v1.5/V15_04_3_CARE_SHEET_READONLY_RECONCILIATION_20261011.md) a recensé les pièges d'une ancienne proposition [#799](https://github.com/hraaaaf/Digital_crown/pull/799) : archive `AUTRE`/insurance ne vaut pas autorité de finalisation, concordance de métadonnées hash sans lecture d'octets insuffisante, risques de chemins et symlinks, contamination inter-tenant et autorisation de retrait. L'état « 04.3 pas encore implémenté » était vrai pour l'ancien master audité, **pas une conclusion sur le master après #837/#882**. #799 est déjà CLOSED **sans** merge ; ses anciens workflow/code/tests restent accessibles à titre historique et ne doivent pas être repris sur master sans nouveau contrôle.

**À retenir comme matrice de régression** : autorité de finalisation et d'autorisation staff, fichier/hash réel, version active, chemins de stockage sûrs, document non révoqué, tenant/patient exact, station identifiée et session bornée, absence de génération clinique par kiosk ; les versions actuelles doivent être testées sur leur HEAD, et non validées par la seule existence de cet audit.

### #846 — Audit Pocket/Companion PWA 2.0 : backlog de risques, pas contrat produit approuvé

Conserver les [deux documents source de #846](https://github.com/hraaaaf/Digital_crown/pull/846) : [proposition PWA multi-profils](https://github.com/hraaaaf/Digital_crown/blob/2b71dfb93fd7d0ecd867e76de539c46780c02db8/docs/audits/DC_POCKET_COMMON_PWA_LOT01_2026_10_12.md) et [audit Companion](https://github.com/hraaaaf/Digital_crown/blob/2b71dfb93fd7d0ecd867e76de539c46780c02db8/docs/audits/PATIENT_COMPANION_MOBILE_AUDIT_2026_10_12.md).

Leur orientation produit proposée : base PWA commune avec droits effectifs configurables et appareils approuvés/révoqués individuellement ; cohérence visuelle Patient, Dentiste, Assistante ; chiffrement/coffre patient et périmètre d'accès séparés des permissions et tokens staff. **Ne jamais dériver la permission patient du seul rôle ou du shell visuel.**

L'audit patient de 2026-10-12 rapporte **huit pistes F01–F08** à réconcilier avec le **code actuel**, en particulier vérité des états hors-ligne/en attente/synchronisé (F01/F02), effacement local explicite (F03), double identité/installation PWA patient vs staff et relance iOS après code à usage unique (F04), distinction 401/403/500/offline (F05), expiration et changement de dossier (F06), annulations/timeout réseau (F07), premier usage réellement testé vs mocks (F08). **Ce sont des constats sur la révision ancienne, pas huit anomalies prouvées toujours présentes après #882.** Les revérifier avant d'ouvrir un correctif.

## 2. Expériences de test FUE/PWA : preuves exactes et limites

- [#839 — FUE 04.3 laboratoire](https://github.com/hraaaaf/Digital_crown/pull/839) : [run #38132306248](https://github.com/hraaaaf/Digital_crown/actions/runs/38132306248) SUCCESS, mais sur une **révision antérieure** `7bf1d358bc97257b2bcb0f863d56c16e2bf5fa91`. La PR HEAD plus récent est `acbe876e0e29d655ee7f859ffe2a6484f77b4b8e`. Les revues internes de la PR indiquent que les contrôles matériels NFC/QR, impression/Pocket et observation patient réel sont **0/10 NON TESTÉS**. Le navigateur Chromium lab ne prouve pas qu'une personne a réellement récupéré un document ; document Station affichait « en cours de construction ». Workflow et scripts originaux restent dans la PR, **non portés sur master**. Les essais terrain appartiennent aux gates physiques correspondants.
- [#843 — appairage réel Safari/iPhone synthétique](https://github.com/hraaaaf/Digital_crown/pull/843) : [run #38227579941](https://github.com/hraaaaf/Digital_crown/actions/runs/38227579941) **FAILURE** sur le SHA exact `1aa7dc8a1e11b054fd40a9a6af8ca12e4f01b1b2`, étape « Require actual paired HTTPS Agenda and responsive nav in WebKit ». **Risque non fermé** par la fusion de #882 et non compensé par un test Chromium. Il faut une preuve valide sur le nouveau code/master et, lorsqu'exigé, le vrai appareil.
- [#845 — première installation WebKit PWA](https://github.com/hraaaaf/Digital_crown/pull/845) : sur `c05329f03c29709b6a9d0ad526cfb0ac6b1f1d73`, [WebKit #38264545242](https://github.com/hraaaaf/Digital_crown/actions/runs/38264545242) **SUCCESS**, [QR synthétique #38264545463](https://github.com/hraaaaf/Digital_crown/actions/runs/38264545463) **SUCCESS**, mais [Settings Security #38264545301](https://github.com/hraaaaf/Digital_crown/actions/runs/38264545301) et [Mobile Pocket Runtime #38264545642](https://github.com/hraaaaf/Digital_crown/actions/runs/38264545642) **FAILURE**. Certains scripts/lifecycle fixes de #845 ne sont pas prouvés inclus dans master. **Ne pas merger/rebaser automatiquement cette ancienne branche**, ni conclure « all green ». Requalifier sur HEAD actuel les assertions en échec avant fermeture.

## 3. Décision de tri et fermeture

- PR chaîne LOT04/Pocket #835/#838/#840/#847/#849/#852/#862/#873/#874/#876/#877/#881 : GitHub les reconnaît déjà MERGED, reprises par l'intégration finale #882.
- PR laboratoire #858/#859/#860/#870/#871 : CLOSED **non merged**, avec commentaires individuels ; leurs variantes B/C/D sont intégrées/modifiées en logiciel, mais pas tous leurs anciens workflows indépendants.
- PR #799 : CLOSED **non merged**, remplacée par une réalisation clinique durcie (#837 puis #882). Ne pas restaurer son ancienne logique.
- PR documentaires #848/#836/#846 : à archiver comme sources datées **uniquement après** création de ce registre de traçabilité. Leurs documents détaillés restent accessibles dans les branches/PR originales ; les risques actuels restent ouverts tant que non revérifiés sur master.
- PR FUE lab #839 : candidat à l'archivage **comme expérience révolue**, avec son run et ses limites sauvegardés ici ; **aucun PASS terrain** accordé.
- PR mobiles #843/#845 : **conserver OPEN/BLOQUÉ À REQUALIFIER** tant que leurs échecs/correctifs et la validation iOS sur le code actuel ne sont pas résolus. L'expérience #845 n'est pas une preuve d'appairage physique iPhone.

## 4. Gates et suite

**REQUIRED à confirmer** : tests de régression exact-HEAD sur l'implémentation active, contrôle de la vraie frontière Station PDF HTTP423, permissions tenant/auth, scénario Mobile/PWA pertinent et revue de la source de risque. **PHYSICAL PASS LOT10 séparé** (deux postes, LAN/TLS/QR et impression/secure release, observateur et artefacts). Jamais d'activation de l'impression clinique, migration patient, environnement cabinet ou Vercel à partir de cette documentation.

**Prochaines actions** : (1) maintenir un seul registre documentaire sans réouvrir les PR historiques ; (2) diagnostiquer les runs rouges #843/#845 et les reproduire, si encore applicables, sur `master` exact dans un environnement synthétique isolé ; (3) planifier les essais terrain LOT10, sans confondre preuve CI et preuve matérielle. Aucun certificat de release ou review indépendante n'est produit ici.

**Double lecture interne (documentaire seulement)** :
- **A / sécurité et clinique** : aucune promotion d'une ancienne autorisation papier, de l'archive `AUTRE` ni d'un partage Pocket en autorisation Station ; maintenir toutes les frontières fail-closed.
- **B / preuves et mobile** : absence d'une même preuve exacte pour le Safari réel, assertions rouges non effacées, captures physiques et validation humaine absentes. Verdict documentaire : **traçabilité établie ; validation mobile et matérielle OUVERTE**.
