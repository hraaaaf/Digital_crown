# Prescription Pharmacology Morocco RCP M1

Status: ACTIVE — M1-A REGULATORY PRESENTATION IDENTITY

## Goal

Construire un snapshot local et versionné des preuves réglementaires AMMPS pertinentes pour la pharmacologie dentaire, sans créer de second moteur de prescription et sans dépendance réseau au runtime cabinet.

## Success

M1 est clos uniquement lorsque chaque présentation dentaire prioritaire possède une identité réglementaire unique, son statut AMM, son statut de commercialisation, sa provenance AMMPS, son état RCP (`PENDING_DOWNLOAD`, `SNAPSHOT_VERIFIED` ou `UNAVAILABLE_VERIFIED`), et lorsque tout RCP local validé possède une empreinte SHA-256 et une date de vérification.

Aucune ligne M1 n'autorise à elle seule une posologie ou un passage vers `AUTO_OK_MAROC`.

## Architecture retenue

- Réutiliser le catalogue unique `backend/services/medication_dict.py`.
- Préserver le `presentation_id` historique pour compatibilité.
- Ajouter un `regulatory_presentation_id` package-level, dérivé au minimum de nom, DCI, dosage, unité, forme, conditionnement et EPI.
- Conserver séparément `amm_status`, `market_status`, `market_status_checked_at`, `rcp_url`, `rcp_snapshot_status`, `rcp_sha256`, `rcp_checked_at`.
- La présence d'un lien RCP n'est jamais assimilée à un RCP téléchargé/validé.
- AMM, commercialisation et disponibilité pharmacie temps réel restent trois notions distinctes.

## Sources officielles vérifiées le 2026-09-15

- AMMPS — Base de données des médicaments : 9 908 présentations ; statut par présentation et téléchargement RCP exposés.
- AMMPS — Liste marocaine des médicaments : statut AMM et statut de commercialisation séparés.
- AMMPS — RMMG, édition projet janvier 2026 : répertoire dynamique des génériques effectivement commercialisés ; ne remplace pas le RCP.

## M1-A — identité réglementaire et statut

Premier lot prioritaire : amoxicilline orale, puis autres antibiotiques dentaires et antalgiques/AINS déjà présents dans M0.

Les variantes de conditionnement doivent rester distinctes réglementairement même si le `presentation_id` historique les déduplique pour l'UI documentaire existante.

## M1-B — snapshot RCP local

Pour chaque présentation retenue :

1. télécharger le RCP depuis la source AMMPS officielle ;
2. conserver localement le document ou un artefact textuel canonique autorisé ;
3. calculer SHA-256 ;
4. enregistrer date de vérification et URL source ;
5. extraire uniquement des champs structurés explicitement présents dans le RCP ;
6. toute donnée absente ou ambiguë reste `PENDING_*` / review, jamais inférée.

## Non-régression obligatoire

- aucun changement DB ;
- aucun changement patient/document ;
- aucun changement UI en M1-A ;
- recherche CNOPS historique inchangée ;
- `presentation_id` historique inchangé ;
- `get_presentation()` reste compatible ;
- aucun nouveau `AUTO_OK_MAROC` ;
- aucun schéma thérapeutique nouveau activé.

## Preuve attendue M1-A

- tests unitaires sur collision de conditionnement ;
- même `presentation_id` historique pour variantes qui le partageaient déjà ;
- `regulatory_presentation_id` distinct par conditionnement ;
- exposition documentaire de `amm_status` / `market_status` sans modification des décisions cliniques ;
- CI complète verte.

## Human gate

Les données RCP extraites qui pourraient modifier une décision clinique passeront par validation médicale avant M2.

Aucun Vercel.
