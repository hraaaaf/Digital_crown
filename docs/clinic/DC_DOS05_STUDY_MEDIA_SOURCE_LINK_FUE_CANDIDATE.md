# DC-DOS-05 — Contrat expérimental étude ↔ médias originaux chiffrés

Statut : **CANDIDATE ISOLÉE**, pas de migration clinique, pas de production, pas de validation médicale.
Base : PR #1244 GREEN, `6b255b662dd7c132ceab6ca9de3da5e4e0cc4371`.
Branche indépendante : `test/dc-dos05-study-media-link-20261109`.

## GOAL / SUCCESS / PROOF

**GOAL** : ne plus déduire l'appartenance d'une photo T0 ou radio T1 à une étude céphalométrique par `timepoint` ou `image_original_path` seul. Lier explicitement une étude, son patient/cabinet, un rôle, un identifiant média ORIGINAL, son SHA-256 chiffré à l'import et la révision scientifique exacte.

**SUCCESS (candidat)** : deux rôles explicites `RADIO_SOURCE` et `PHOTO_CONTEXT` écrits une seule fois. Toute lecture revalide la propriété patient/cabinet/étude, la révision scientifique active, la catégorie, le SHA du média original et les octets AES-GCM déchiffrés. Si une pièce manque, réponse 4xx, aucun rattachement implicite.

**PROOF prévu** : FUE HTTP authentifié JWT / FastAPI véritable, base SQLite volatile, images entièrement synthétiques. Matrice négative A→B, cabinet X, mauvaise étude, mauvais rôle, ancienne révision, dérivé miniature, collision de rebind, altération SHA ; désactivation par défaut hors banc expérimental.

## Surface technique candidate

- Table `CephaloStudyMediaBinding` : `employer_id`, `patient_id`, `study_id`, `asset_id`, `role`, `asset_sha256`, `revision`, `created_by`, `created_at`. Unicité SQL `(study_id, role)` ; l'API n'offre aucune mutation/suppression.
- `backend/services/cephalo_study_media_binding.py` : preuve du graphe scientifique `EVIDENCE_GRAPH_V1` et révision `VERIFIED`; contre-vérification de l'original Media Core et contenu chiffré ; échec fermé.
- `backend/routers/cephalo_study_media_binding.py` : uniquement monté dans le FUE synthétique. Le module n'est **pas** ajouté à `backend/routers/__init__.py` ; il exige simultanément `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=true`, `DC_DOS05_FUE_ONLY=1`.
- `backend/models_cephalo_study_media.py` n'est **pas** importé dans `backend/__init__.py` ; la nouvelle table n'est **pas** introduite dans le schéma clinique existant.
- Contrôle de concurrence : unicité SQL et `IntegrityError` → HTTP 409.
- `ClinicalAsset.timepoint` est un libellé longitudinal, **jamais** une clé étude. `original_filename`, `source_ref` et le chemin historique ne donnent pas d'autorité de liaison.

## Ce que la preuve ne peut pas dire

Le rattachement prouve une **association explicite et l'intégrité actuelle des médias**. Il **ne prouve pas** que les landmarks, mesures, calibrations ou PDF déjà enregistrés ont été calculés à partir de ces octets. Pour cela, il manque une chaîne d'acquisition/tracé source-lock et sa preuve transitivement vérifiée. `clinical_release=false` et `cephalo_computation_from_source_proven=false` demeurent obligatoires. Aucun migration/déploiement/EXE/merge.

La contrainte SQL unique ne protège pas contre un administrateur SQL modifiant directement une ligne ; la politique « write-once » est celle de l'API et doit être complétée par des protections d'audit et une stratégie DB explicitement approuvée avant production.

## HUMAN GATE / Next exact

1. Atteindre GREEN sur le FUE dédié, vérifier les résultats du nouveau HEAD.
2. Revoir indépendamment la conception et la compatibilité SQLite/PostgreSQL, la stratégie de migration + rollback + sauvegarde/restauration.
3. Après autorisation explicite, intégrer réellement la source dans le pipeline céphalométrique et son UI ; FUE navigateur complet séparé avant prétention de disponibilité clinique.
4. Fusion et installation uniquement sur autorisation explicite ; ce candidat ne change pas le runtime courant.
