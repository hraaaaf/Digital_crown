# Prescription Pharmacology Morocco Coverage

Status: VALIDATED — M0 PRE-MERGE

## Goal

Établir pour Digital Crown une couverture pharmacologique dentaire exhaustive, Morocco-first, sans gap silencieux et sans inventer indication, schéma, statut réglementaire, disponibilité ou sécurité patient.

M0 ne modifie aucun comportement clinique du runtime.

## Résultat M0 vérifié

- 50 lignes molécules/contextes dans `PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_MATRIX.json`.
- 22 indications/protocoles dentaires dans `PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_INDICATIONS.json`.
- 50 lignes sécurité dans `PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_SAFETY.json`.
- 6 dimensions sécurité obligatoires par ligne : âge/poids, grossesse-allaitement, rénal, hépatique, allergies, interactions.
- 300 états sécurité explicites au total ; une information non résolue reste `PENDING_*`.
- ledger de preuves dans `PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_EVIDENCE.json` avec distinction `CROSS_CHECKED` / `PRIMARY_ONLY`.
- zéro nouveau `AUTO_OK_MAROC` en M0.
- zéro changement DB, données patients, documents, UI/UX ou déploiement.

## Human gate médical

VALIDÉ par le praticien le 2026-09-15.

Univers clinique M0 validé :

- `AUTO_OK_MAROC` : 0 indication.
- `PROPOSE_CONFIRM` : 4 indications.
- `REVIEW_ONLY` : 14 indications.
- `NOT_SUPPORTED` : 4 indications.

Cette validation porte sur l’univers clinique et les niveaux de prudence. Elle ne valide aucune nouvelle posologie marocaine automatique.

## Invariants verrouillés

1. AMM enregistrée ≠ commercialisation ≠ disponibilité pharmacie temps réel.
2. Une recherche négative n’est jamais une preuve d’absence.
3. RCP/AMMPS Maroc prime pour le produit et la présentation.
4. Le guide national bucco-dentaire 2014 définit un périmètre historique utile mais ne suffit pas seul à automatiser une posologie en 2026.
5. Les sources internationales restent support/cross-check lorsqu’une preuve marocaine actuelle manque.
6. Ambulatoire, chairside et urgence cabinet restent trois périmètres distincts.
7. Un abcès localisé ne déclenche pas automatiquement un antibiotique.
8. Une infection sévère avec red flags reste une voie urgence/referral, pas un calcul ambulatoire de dose.
9. Toute dimension sécurité non prouvée reste explicite et fail-closed.
10. Aucun passage vers `AUTO_OK_MAROC` sans preuve marocaine adéquate au niveau indication + présentation + population.

## Hiérarchie des preuves

1. `MOROCCO_RCP_CURRENT` — RCP AMMPS de la présentation.
2. `MOROCCO_AMMPS_CURRENT` — identité, dosage, forme, statut AMM/commercialisation, lien RCP.
3. `MOROCCO_RMMG_2026` — génériques effectivement commercialisés dans le périmètre du répertoire.
4. `MOROCCO_DENTAL_GUIDE` — périmètre dentaire national historique.
5. `MOROCCO_BO_SGG` — recoupement réglementaire/prix, jamais source de posologie.
6. `INTERNATIONAL_SUPPORT` — support/cross-check uniquement.

## Sources Maroc structurantes vérifiées M0

- AMMPS base publique médicaments : 9 908 présentations observées le 2026-09-15, avec statut par présentation et liens RCP.
- RMMG projet janvier 2026 : 312 substances/groupes affichés lors de la vérification ; AMMPS le décrit comme dynamique et centré sur les génériques effectivement commercialisés.
- Guide de promotion de la santé bucco-dentaire du Ministère de la Santé, édition 2014.
- Bulletin Officiel/SGG utilisé en recoupement lorsque pertinent.

## Preuve CI exacte

HEAD fonctionnel M0 certifié : `842cb896057c2e7f0a0a2d75e8af469c0ddc954b`.

Workflows exact-head vérifiés :

- CI #4366 — SUCCESS.
- Cabinet Upgrade PostgreSQL Certification #766 — SUCCESS.
- Catalog Connected Truth Certification #1268 — SUCCESS.
- T2 Runtime Browser Certification #3251 — SUCCESS.
- M6-I Biometric Passkey Certification #2051 — SKIPPED attendu.

La CI #4366 inclut la régression backend complète DB/patients/documents, les tests frontend, le build, la garde production et les certifications M4-A/M4-B/M4-C.

## Architecture cible M1

Le cabinet reste local/on-premise et ne dépend jamais du site AMMPS au moment de prescrire.

M1 doit construire un snapshot local versionné des preuves AMMPS/RCP, présentation par présentation, avec au minimum :

`evidence_version`, `molecule`, `composition`, `presentation`, `route`, `form`, `age_rule`, `weight_rule`, `regimen`, `duration`, `pregnancy_rule`, `breastfeeding_rule`, `renal_rule`, `hepatic_rule`, `allergy_rule`, `interaction_rules`, `amm_status`, `market_status`, `epi`, `ean13`, `rcp_url`, `rcp_checked_at`, `source_hash`, `automation_tier`, `decision_reason`.

Le réseau sert uniquement à mettre à jour le référentiel ; l’Ordonnance consomme le snapshot local validé.

## Séquence restante

1. Certifier ce commit documentaire final.
2. Passer #516 ready.
3. Squash merge M0 sur `master` avec expected HEAD exact.
4. Vérifier le push CI post-merge.
5. Ouvrir M1 depuis le merge SHA réel.
6. Construire le snapshot local AMMPS/RCP et ses tests d’intégrité, sans nouvelle auto-proposition clinique.
7. Seulement après M1 validé : M2 antibiothérapie curative + prophylaxie, puis familles suivantes.

## Fichiers M0 canoniques

- `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_COVERAGE.md`
- `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_MATRIX.json`
- `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_INDICATIONS.json`
- `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_SAFETY.json`
- `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_EVIDENCE.json`

M0 est cliniquement validé et techniquement certifié sur son HEAD fonctionnel. Le merge reste conditionné à la certification du présent commit documentaire final.
