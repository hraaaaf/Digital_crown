# Restauration guidée — CLOSEOUT

Date : 2026-08-22
Repo : `hraaaaf/Digital_crown`
PR : #213

## Goal

Permettre à un administrateur de restaurer un cabinet de façon sûre, explicable et réversible, sans écraser l’état courant sans point de secours vérifié.

## Résultat produit certifié

- préflight sans mutation ;
- validation checksum, anti-path-traversal, symlink, archive bomb et basenames ambigus ;
- validation DB SQLite/SQLCipher + schéma Digital Crown minimal (`users`, `patients`) ;
- sauvegardes historiques DB-only restaurables avec médias explicitement préservés ;
- archives manifestées DB + médias supportées ;
- jobs de restauration scopés au cabinet qui a effectué le préflight ;
- flow explicite : analyser → préflight → préparer la restauration → saisir `RESTAURER` → apply ;
- package revalidé avant préparation puis avant apply ;
- point de secours DB créé et vérifié avant toute bascule destructive ;
- après arrêt du backend, DB + WAL exacts sont repris et vérifiés avant remplacement ;
- médias courants protégés par empreinte puis renommage atomique lorsque le package les remplace ;
- candidate DB restaurée en staging, validée, puis publiée par `os.replace` ;
- apply destructif fail-closed hors exécutable cabinet ;
- worker détaché avant import FastAPI ;
- redémarrage contrôlé + smoke check `/health` ;
- rollback DB + médias puis second smoke check en cas d’échec ;
- état persistant/auditable sans exposer clés ni chemins sensibles.

## BEFORE / Goal visuel

BEFORE #22 : run `32529921293` — SUCCESS.
Base immuable : `99c2aa32c6b145804467f7f38ea10722c2714e78`.

Viewports : 1440×1200, 768×1200, 390×1200, 360×1200, 320×1200.

Référence visuelle : `docs/settings/GUIDED_RESTORE_MOCKUP.svg`.
Goal canonique : `docs/settings/GUIDED_RESTORE_GOAL.md`.

## HEAD produit certifié

`453b5213f728b87bb64303cb0f06417b2b3d6fe2`

Dernier delta produit depuis `9875f9c98050601515b0ad0b46bae4ab4c20d446` : 1 commit, 6 fichiers seulement.

Avant publication, le correctif final a été reconstruit hors branche et a passé **16/16 tests ciblés**.

## AFTER final

Settings Guided Restore AFTER #3 : run `32559882456` — **SUCCESS**.
Artifact : `9472491713`.
Digest : `sha256:adb6a3ef4b5ab0f8848dcbf7ba442f150b5a0160a64adadb0ef66066d77c2dc8`.

Viewports inspectés : 1440 / 768 / 390 / 360 / 320.

- captures : 5/5 ;
- overflow horizontal : 0/5 ;
- page errors : 0/5 ;
- HTTP 5xx : 0/5 ;
- request failures : 0/5 ;
- étape « Préparer la restauration » visible et séparée de la confirmation finale ;
- responsive lisible jusqu’à 320 px ;
- intégration cohérente avec Sauvegarde, Companion Mobile et Journal d’Audit.

Score visuel : **9,4/10**.

Réserve visuelle non bloquante : la surface devient naturellement dense à 320 px, mais sans overflow, coupure fonctionnelle ni ambiguïté de sécurité.

## Gates exact HEAD produit

- Settings Guided Restore AFTER #3 `32559882456` — SUCCESS ;
- CI #1590 `32559882536` — SUCCESS ;
- Settings Security Visual Certification #10 `32559882581` — SUCCESS ;
- Settings RBAC Visual Certification #146 `32559882403` — SUCCESS ;
- T2 Runtime Browser Certification #789 `32559882450` — SUCCESS ;
- Catalog Connected Truth Certification #62 `32559882549` — SUCCESS ;
- Patient P7 Final Certification #88 `32559882494` — SUCCESS ;
- Settings R11 TemplateBuilder Dependency Audit #8 `32559882479` — SUCCESS.

Le workflow AFTER confirme également compilation des entrypoints, tests ciblés de restauration et build frontend.

## Dette non bloquante

Le format historique de sauvegarde média est encore un payload Fernet monolithique : son déchiffrement nécessite de matérialiser le contenu chiffré/déchiffré avant lecture ZIP. Ce point est acceptable pour le contrat actuel mais n’est pas idéal pour des archives médias gigantesques ; une future évolution de format streaming/chunked devra être traitée comme un chantier séparé, sans invalider la sûreté transactionnelle certifiée ici.

## Décision

**Restauration guidée = CLOSED / CERTIFIÉE** au HEAD produit `453b5213f728b87bb64303cb0f06417b2b3d6fe2`.

La PR peut être mergée après vérification que le commit de closeout ne modifie que la documentation. Les preuves exact-HEAD produit restent applicables à un delta docs-only.

Aucun Vercel.
