# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-15
Status: ACTIVE — handover only, no runtime change

## Goal global
Construire une couverture pharmacologique dentaire exhaustive et systématiquement sourcée Maroc, avec séparation stricte entre preuve réglementaire, indication, dose et activation clinique.

## Invariants
- Local/on-premise. Aucun changement SaaS/Vercel.
- Préserver DB, données patients, documents et fonctionnalités validées.
- Aucun AUTO_OK ni activation clinique sans preuve Maroc suffisante et revue humaine/scientifique requise.
- Recherche négative != preuve d'absence.
- Aucune disponibilité temps réel inventée.
- `scientific-reviewer` indépendant requis avant merge de toute implémentation scientifique. L'auteur de l'implémentation ne peut pas satisfaire lui-même cette gate.

## Références à lire au démarrage
1. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_COVERAGE.md`
2. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md`
3. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`
4. `.claude/rules/scientific-engineering.md`
5. `.claude/agents/scientific-reviewer.md`
6. `.claude/agents/pharmacology-engineer.md`

## État vérifié de master
- `master`: `8f74464998a721414e67957e0c9346f6a67efdb2`
- Dernier commit master observé: `docs(cephalo): resync canonical registry on current master (#515)`
- Le commit master ci-dessus ne modifie pas le chantier pharmacologie.

## M1-A — CLOSED / MERGED
- Snapshot AMMPS actuel package-level.
- 8 présentations amoxicilline exactes.
- Merge master: `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- Post-merge CI #4392 verte.

## M1-B0 — CLOSED / MERGED
- Manifest RCP fail-closed créé.
- 8 entrées amoxicilline initiales `PENDING_DOWNLOAD`.
- Merge master: `81bf142021cdf4770e9c6ca92078306ac4898783`.

## M1-B1 — CLOSED / MERGED
- Queue Wave 1 documentaire créée.
- Merge master: `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Molécules Wave 1: paracetamol, ibuprofen, amoxicillin, penicillin_v, metronidazole, clarithromycin, clindamycin.

## PR #520 — M1-B2 first verified RCP capture transport
Branch: `feat/prescription-pharmacology-morocco-rcp-first-capture`
HEAD: `15430e879f8e763e55f117842ad27364df8257d5`
State: OPEN / Ready / mergeable=true au dernier check
Changed files: 3

### Implémentation
`backend/services/medication_rcp_manifest.py`:
- validation stricte date `YYYY-MM-DD`;
- URL HTTPS AMMPS officielle obligatoire;
- chemin local sûr sous `backend/data/rcp/*.pdf`;
- artefact local doit exister;
- octets locaux doivent commencer par `%PDF-`;
- SHA-256 recalculé depuis le vrai fichier local;
- `snapshot_is_verified(...)` relit le fichier et échoue si absent/hash faux/extension fausse/contenu non-PDF;
- `prepare_verified_snapshot_entry(...)` est offline-only, sans persistence automatique, sans extraction clinique, sans mutation de l'entrée source.

### Tests
Couvrent notamment: missing artifact, wrong hash, unsafe path, malformed date, non-official URL, wrong extension, fake PDF, byte mismatch, polluted source.

### Certification exact-head #520
HEAD exact `15430e879f8e763e55f117842ad27364df8257d5`:
- CI #4437 SUCCESS
- Cabinet Upgrade PostgreSQL #829 SUCCESS
- T2 Runtime Browser #3314 SUCCESS
- M6-I #2114 SKIPPED attendu

### Gates restantes #520
- Aucun review submission GitHub au dernier check.
- Gate repo `scientific-reviewer` indépendant NON satisfaite.
- Aucun vrai PDF RCP AMMPS capturé.
- NE PAS merger tant que la revue scientifique indépendante requise n'existe pas.

### Première cible de capture
- Molécule: amoxicilline
- Présentation: `AMOXICILLINE SP 1 G COMPRIME DISPERSIBLE BOITE DE 12`
- regulatory presentation id: `ammps-reg:6fd268f476e7efe0c11f0c4b`
- page source AMMPS: `https://www.ammps.gov.ma/recherche-medicaments?page=42`
- bouton `Télécharger RCP` observé, mais URL réelle du PDF non exposée par les transports disponibles.
- Ne jamais inventer le `rcp_url`.

## PR #522 — Wave 1 evidence refresh
Branch: `docs/pharmacology-wave1-ibuprofen-evidence-refresh`
HEAD: `0f9af14763bc6d85bc3a028d12f186c55e7ff746`
Base: master `8f74464998a721414e67957e0c9346f6a67efdb2`
State: OPEN / Ready / mergeable=true au dernier check
Changed files: 2 seulement
Runtime behavior change: false

### Modifications documentaires
- `ibuprofen`: `PENDING_RCP_LINK_CONFIRMATION` -> `READY_FOR_CAPTURE_TRANSPORT`
  - preuve actuelle AMMPS: page recherche médicaments 27 avec présentations orales et contrôle `Télécharger RCP`;
  - page Liste Marocaine des médicaments 68 confirme le statut package-level.
- `metronidazole`: `PENDING_CURRENT_PAGE_CONFIRMATION` -> `PENDING_RCP_LINK_CONFIRMATION`
  - RMMG AMMPS janvier 2026 page 11: présentations orales 500 mg avec EAN, notamment METROZAL, NIDAZOL, ZYRDOL, FLAGYL, METROGYL.
- `clindamycin`: reste `PENDING_CURRENT_PRESENTATION_DISCOVERY`.
  - aucune présentation orale actuelle AMMPS suffisamment prouvée;
  - recherches secondaires n'ont donné que formes topiques; cela n'est PAS une preuve d'absence.

### CI #522 au dernier check
HEAD exact `0f9af14763bc6d85bc3a028d12f186c55e7ff746`:
- CI #4447 IN_PROGRESS
- Catalog Connected Truth #1301 SUCCESS
- T2 Runtime Browser #3323 SUCCESS
- Cabinet Upgrade PostgreSQL #838 SUCCESS
- M6-I #2123 SKIPPED attendu

## Outils / transport RCP
- Firecrawl n'est pas installé.
- TinyFish a été suggéré récemment; ne pas re-suggérer immédiatement.
- Le transport web actuel confirme pages/boutons mais ne révèle pas le href PDF AMMPS de façon fiable.
- Un crawler/navigateur interactif peut être utilisé seulement s'il est réellement disponible; ne jamais simuler une capture.

## Next exact
1. Vérifier UNE FOIS la CI exact-head de #522 `0f9af147...`.
2. Si #522 est verte: ne pas merger sans accord utilisateur explicite; préparer merge squash exact-head seulement après accord.
3. Après merge #522: vérifier post-merge CI une fois et master réel.
4. Re-vérifier #520 contre master (mergeable/divergence). Ne rebase pas si inutile.
5. Obtenir une vraie revue indépendante `scientific-reviewer` pour #520; ne jamais auto-valider cette gate.
6. Capturer le vrai PDF RCP AMMPS de la cible amoxicilline, stocker sous `backend/data/rcp/*.pdf`, calculer SHA-256, vérifier octets locaux, puis promouvoir UNE entrée exacte à `SNAPSHOT_VERIFIED`.
7. Ajouter tests hash/file et mettre à jour le canonical M1.
8. CI exact-head -> accord utilisateur avant merge -> merge -> post-merge -> lot suivant.

## Interdits
- Pas de merge sans accord explicite utilisateur.
- Pas de Vercel deploy.
- Pas de dose/durée/indication/AUTO_OK ajoutée dans M1 documentaire.
- Pas d'inférence libre de sévérité ni d'âge/poids.
- Pas de claim `SNAPSHOT_VERIFIED` sans fichier PDF réel + hash correspondant.

## Critère de succès M1-B2
Une entrée RCP exacte est promue à `SNAPSHOT_VERIFIED` uniquement si le PDF AMMPS réel existe localement, son URL officielle est connue, la date est valide, le SHA-256 correspond au fichier relu, les tests passent, la revue scientifique indépendante est satisfaite et la CI exact-head est verte.
