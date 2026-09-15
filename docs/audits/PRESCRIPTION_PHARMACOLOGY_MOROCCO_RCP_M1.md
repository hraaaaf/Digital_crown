# Prescription Pharmacology Morocco RCP M1

Status: ACTIVE — M1-A IMPLEMENTED / FINAL EXACT-HEAD CI REQUIRED

## Goal

Construire un snapshot local et versionné des preuves réglementaires AMMPS pertinentes pour la pharmacologie dentaire, sans créer de second moteur de prescription et sans dépendance réseau au runtime cabinet.

## Success

M1 est clos uniquement lorsque chaque présentation dentaire prioritaire possède une identité réglementaire unique, son statut AMM, son statut de commercialisation, sa provenance AMMPS, son état RCP (`PENDING_DOWNLOAD`, `SNAPSHOT_VERIFIED` ou `UNAVAILABLE_VERIFIED`), et lorsque tout RCP local validé possède une empreinte SHA-256 et une date de vérification.

Aucune ligne M1 n'autorise à elle seule une posologie ou un passage vers `AUTO_OK_MAROC`.

## Architecture retenue

- Réutiliser le catalogue unique `backend/services/medication_dict.py`.
- Préserver le `presentation_id` historique pour compatibilité.
- Ajouter un `regulatory_presentation_id` package-level, dérivé au minimum de nom, DCI, dosage, unité, forme, conditionnement et EPI.
- Les APIs historiques `search`, `get_presentation` et `validate_dosage` ignorent le snapshot AMMPS courant M1 tant qu'une migration explicite n'est pas validée.
- Les APIs réglementaires M1 sont fail-closed sur le snapshot AMMPS courant daté uniquement : aucune absence ne peut retomber silencieusement vers CNOPS ou RMMG historique.
- Conserver séparément `amm_status`, `market_status`, `market_status_checked_at`, `rcp_url`, `rcp_snapshot_status`, `rcp_sha256`, `rcp_checked_at`.
- La présence d'un lien RCP n'est jamais assimilée à un RCP téléchargé/validé.
- AMM, commercialisation et disponibilité pharmacie temps réel restent trois notions distinctes.

## Sources officielles vérifiées le 2026-09-15

- AMMPS — Base de données des médicaments : 9 908 présentations affichées lors de la vérification ; statut par présentation et téléchargement RCP exposés.
- AMMPS — Liste marocaine des médicaments : statut AMM et statut de commercialisation séparés.
- AMMPS — RMMG, édition projet janvier 2026 : répertoire dynamique des génériques effectivement commercialisés ; ne remplace pas le RCP.

## M1-A — identité réglementaire et statut

Implémentation actuelle :

- source locale `backend/data/medications_ma_ammps_current_2026.json` intégrée au catalogue documentaire unifié ;
- 8 présentations d'amoxicilline seedées avec statut de commercialisation vérifié au 2026-09-15 ;
- statut AMM conservé uniquement lorsqu'il est explicitement exposé par la source, sinon `PENDING_VERIFICATION` ;
- RCP non téléchargé = `PENDING_DOWNLOAD`, `rcp_sha256 = null`, `rcp_checked_at = null` ;
- `regulatory_presentation_id` distinct par conditionnement ;
- packaging PyInstaller mis à jour pour embarquer le snapshot ;
- tests de non-régression sur identité historique, isolement du snapshot courant, collision de conditionnement, packaging et fail-closed réglementaire.

La variante `DISPAMOX`, présente dans l'ancien référentiel, sert de test de sécurité : si elle est absente du snapshot AMMPS courant M1, l'API réglementaire retourne aucun résultat au lieu de réutiliser une preuve historique.

M1-A ne modifie aucune décision clinique, posologie, durée, tier d'automatisation, donnée patient, document clinique, schéma DB ou UI.

## M1-B — snapshot RCP local

Wave 1 prioritaire, car déjà utilisée ou directement pertinente dans le moteur dentaire :

1. paracétamol ;
2. ibuprofène ;
3. amoxicilline ;
4. phénoxyméthylpénicilline ;
5. métronidazole ;
6. clarithromycine ;
7. clindamycine.

Pour chaque présentation retenue :

1. récupérer le RCP depuis la source AMMPS officielle exacte ;
2. conserver un manifest local versionné léger avec identité réglementaire, URL officielle, date et état de capture ;
3. calculer SHA-256 du RCP capturé ;
4. extraire uniquement les champs structurés explicitement présents dans le RCP ;
5. conserver le PDF brut hors runtime si nécessaire, sans perdre sa provenance/hash ;
6. toute donnée absente ou ambiguë reste `PENDING_*` / review, jamais inférée.

Une source secondaire peut servir de recoupement documentaire, mais ne peut jamais remplacer l'AMMPS comme preuve réglementaire primaire d'activation.

## Non-régression obligatoire

- aucun changement DB ;
- aucun changement patient/document ;
- aucun changement UI en M1-A ;
- recherche CNOPS/RMMG historique inchangée ;
- `presentation_id` historique inchangé ;
- `get_presentation()` historique reste compatible ;
- APIs réglementaires sans fallback historique ;
- aucun nouveau `AUTO_OK_MAROC` ;
- aucun schéma thérapeutique nouveau activé.

## Preuve M1-A

État actuellement vérifié :

- PostgreSQL certification #782 : success sur le HEAD code `4f49b67b7c304c432bd4954dd08620559fdc426f` ;
- Catalog Connected Truth #1281 : success sur le même HEAD code ;
- T2 Runtime #3267 : success sur le même HEAD code ;
- CI #4383 de ce HEAD code : cancelled après création du commit de closeout, donc non retenue comme preuve ;
- M0 post-merge CI #4369 : success.

Le HEAD final de closeout documentaire doit recevoir sa propre certification exact-head avant ready/merge. Une certification d'un HEAD antérieur ne vaut pas preuve pour le HEAD final.

## Human gate

Les données RCP extraites qui pourraient modifier une décision clinique passeront par validation médicale avant M2.

Aucun Vercel.
