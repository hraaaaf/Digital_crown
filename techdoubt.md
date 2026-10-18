# TECHDOUBT — Digital Crown

## LOT05.7-D — 2026-10-18 — Alembic PostgreSQL de laboratoire et isolation inter-cabinets

**Statut clinique NO-GO ; réserves OUVERTES.** Le laboratoire #05.7-D vise le vrai head Alembic `neo000000031` dans un PG18 CI isolé, snapshot/restauration sur deuxième DB et lignes ORM exclusivement fictives. Cela ne certifie ni une installation en exploitation, ni des données sources tierces, ni SQLCipher Cabinet/BackupService/media. Le workflow ne doit jamais migrer des fichiers de production.

**Risque CI / provenance d'image :** le registre ECR du digest PostgreSQL précédemment utilisé a renvoyé `toomanyrequests: Data limit exceeded` sur les runs [#39158998231](https://github.com/hraaaaf/Digital_crown/actions/runs/39158998231) et [#39159152947](https://github.com/hraaaaf/Digital_crown/actions/runs/39159152947), avant tout test. Remplacement limité au workflow LOT05.7-D par la référence `postgres:18` du workflow 05.6 préexistant, dont la **version majeure est vérifiée à l'exécution** ; ce tag mobile ne constitue PAS un pin immuable et devra être re-pinné à un digest vérifié avant toute promotion du protocole. Aucune altération du runtime.

**Risques / BLOCKERS** : FKs de `appointments.patient_id` peuvent autoriser un patient d'un autre `employer_id` malgré `appointments.employer_id`; démontrer l'anomalie en transaction rollback et exige un veto runtime avant tout import réel. La présence de tables/`alembic_version` ne prouve ni conformité de données historiques, ni relations/praticiens/radiographies/factures, ni propriétaire authentifié, ni provenance et conformité, ni isolement de Windows, ni sauvegarde cohérente chiffrée réelle, ni reprise SQLCipher WAL, ni RPO/RTO / reparse/FSYNC ni revue humaine. Les chemins de documents de fixture sont volontairement inexistants et aucun média n'est restauré : cette absence est un BLOQUANT clinique, même si le hash métadonnée est préservé. Le laboratoire PostgreSQL seul ne vaut pas certification SQLCipher. PR empilées #963/#964/#965 non mergées.


## LOT05.7-C — 2026-10-18 — Preuve laboratoire SQLCipher / PostgreSQL ≠ restauration clinique

**STATUS OPEN/NO-GO clinique, même si les tests 05.7-C deviennent verts.** Deux suites test-only distinctes : une DB SQLCipher temporaire chiffrée avec sa clé générée pendant les tests, copiée uniquement hors ligne après checkpoint WAL + fermeture ; une base PostgreSQL 18 temporaire dans un service CI isolé, sauvegardée au format `pg_dump -Fc` puis `pg_restore` dans une autre DB fictive. Les schémas inventés (patients, RDV, praticiens, actes, paiements, références médias) sont *représentatifs* d'une partie des relations, et non le schéma réel Alembic `neo000000031`. Les empreintes, comptes, FK, tests corruption et processus frais ne certifient ni source réelle, ni restauration du véritable Cabinet.

**BLOCKERS / dossiers à prouver ultérieurement** : cohérence multi-moteurs et SQLCipher WAL en ligne ; `BackupService`, `guided_restore`, archives/chiffrement médias réels ; snapshot physique de toute la base et non d'un sous-ensemble inventé ; restauration sur copie isolée de la vraie technologie autorisée et son identifiant tenant, vraie intégrité documentaire/financière, sauvegarde d'assets externes, versionnement PostgreSQL 18 et Alembic, RPO/RTO, protection NTFS ACL/reparse/TOCTOU, fsync/crash matériel, concurrence, remappage praticien/doublons, légalité/provenance des sources, authentification propriétaire/cabinet et décision humaine. Une archive ZIP fictive non chiffrée ne certifie pas la confidentialité de vrais médias. Un dump dont on recalcule le SHA après modification n'a pas une autorité de provenance indépendante. **Aucune route d'import, API production ni permission d'import réel ne peut dépendre de ces suites.**

**CI** : job SQLCipher Windows/Linux et job PostgreSQL 18 doivent être exécutés au HEAD exact, sans skip et sans artefact médical ; si la CI reste incomplète, statut BLOQUÉ ASYNCHRONE. Nouveaux tests ne modifient ni schéma applicatif ni réel patient. Réserve maintenue.


## LOT05.7-B — 2026-10-18 — SQLite WAL lab ≠ preuve clinique de restauration

**Status: OPEN / NO-GO real import.** Nouveau laboratoire standard-library, fichiers temporaires exclusivement fictifs, 100 patients + 200 RDV : vraie API SQLite backup et restauration sur copie distincte, preuve d'un WAL actif, crash de processus / rollback, replay de lot, empreinte SHA-256 du fichier et digest des lignes, FK composite cross-tenant. La CI exacte Linux/Windows 3.11/3.12 doit confirmer l'exécution du nouveau code, pas seulement le prototype local. Un éventuel cas symlink Windows `SKIP` laisse le risque reparse/junction non testé.

**BLOCKERS opérationnels** : SQLCipher du cabinet, PostgreSQL réel / PG18, clés chiffrement et coffre docs, staging de copies autorisées, vraie restauration indépendante d'une copie représentative, Alembic complet et données médicales/financières/médias non concernés. La vérification du SHA attendue depuis une même source non signée n'est pas une preuve de provenance ; le simple contrôle `exists()` avant `os.replace()` est sujet aux races sous concurrence/NTFS reparse, ne certifie ni CAS atomique de restauration, ni crash électrique/fsync du répertoire, ni RPO/RTO. Un fichier SQLite fictif avec marqueur reste une fixture, **pas un adaptateur sûr de données réelles**. Tout branchement à l'API de production est interdit avant un nouveau contrat distinct et gates human/backup/tenant. Aucun import réel, fusion ou déploiement autorisé.


## LOT05.7-A — 2026-10-18 — Réserves import clinique et preuves insuffisantes

**STATUS: OPEN / NO-GO**. L'évaluateur `legacy_import_certification_gate_v15.py` ne vérifie QUE la cohérence de métadonnées déclarées (digest, revision, compteurs, attestations auto-déclarées). Un opérateur malveillant peut inventer toutes les affirmations ; aucune authentification runtime, signature, staging source réel, attestation physique tenant, sauvegarde/restauration indépendante, rapport de dry-run réel, décision humaine ou autorisation de migration n'est établie par ce module. `claims_coherent=true` n'a AUCUNE valeur d'autorisation. La sérialisation du rapport et ses propriétés d'autorisation demeurent systématiquement False.

**Risque BLOCKER** : ne pas connecter cette fonction à une route d'activation. La future migration nécessite des preuves issues d'acteurs et processus séparés, l'impossibilité de confondre source et cible, certification d'une restauration sur copie isolée, journal de provenance lié au cabinet authentifié, double protection contre import cross-tenant, contraintes d'unicité et replay sur DB, plan de rollback/compensation, correspondances patient/praticien/RDV/actes/finances/médias, gestion juridique de confidentialité, approbation humaine distincte. Le schéma cible y est temporairement épinglé `neo000000031`; toute évolution Alembic doit bloquer et imposer une revue explicite. Les tests statiques de routes ne suffisent pas à prouver l'absence d'une route d'import via un autre routeur.

**Validation** : 05.7-A exécute uniquement tests pure-Python/AST sur contenu de dépôt, sans source ou DB clinique ; CI exacte branche PR à vérifier. Réserve maintenue jusqu'à preuves matérielles des gates 05.7-B/C et accord explicite.


## GLOBAL-G10-S / LOT10 — 2026-10-18 — Two-agent isolation requirement withdrawn

**Status: RESOLVED AS A FALSE DEPENDENCY (doctrine correction, not proof of a completed FUE).**

**Previous concern:** The merged PR #960 required two AI BLIND USER agents running in independent contexts, with separate browsers and withheld reports. That had been documented as a blocking precondition even for ordinary internal adversarial review. The product owner clarified that the **same ChatGPT conversation should perform both specialized perspectives A/B itself** rather than waiting for humans or two separate AI agents.

**Resolution rule:** `AGENTS.md`, `.claude/rules/execution-scoring-verification.md` and `docs/quality/REALITY_PROOF_GATE.md` now instruct the assistant to write two distinct, task-specific *internal adversarial* reviews, correct/test, rerun on new HEAD and confirm. This is not evidence of two genuinely independent reviewers; it is sufficient for the **internal A/B double-review procedure**. Self-review is capped at 9.4/10 and normal VERIFIED starts at 9.0/10 when required proofs/gates pass. No external reviewer or two-agent orchestration is a prerequisite.

**Distinct unclosed verification work — GLOBAL-G10-S:** Inventory V1+V1.5 routes/features, execute actual frontend/backend FUE journeys on fictitious tenants starting at login (or a public entry where applicable), preserve BEFORE/ACTION/AFTER, negative RBAC/tenant checks, exact-HEAD evidence and CI statuses. **These tests have NOT been executed by this documentation correction.** An imagined browser session or two written perspectives are not executable test proof.

**Unchanged gates:** Specifically required human clinical/regulatory/visual approvals and LOT10 hardware/person-on-device observations remain separate from conversation-based A/B review. No deployment, merge or clinical activation is authorized by this documentation.

**Historical origin:** PR #960, master merge `3cbd1d83cdbcbf97e71019a3182f4699d9645421`. This file supersedes the inaccurate "two-agent independence not yet demonstrated" as an *internal review blocker*.
