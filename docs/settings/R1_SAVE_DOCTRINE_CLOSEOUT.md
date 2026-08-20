# R1 — Shell / doctrine de sauvegarde — Closeout

Date : 2026-08-20
Repo : `hraaaaf/Digital_crown`
PR : #194
Base BEFORE : `2a6bfd8a10baddf770fed5e2ffbecc3f65f4468d`
HEAD produit certifié : `e472ec47f411850f3270335fd92278c1c08b4fc5`
HEAD final produit + harness : `10ca5475279f579a841bbcce041ffcb7fb6b3f5e`
Statut : **CERTIFIED — READY TO MERGE**

## Goal

Unifier la doctrine de sauvegarde des Réglages : une sauvegarde partagée explicite pour Profil / Design & Ambiance / Performance & Assistance, aucune fausse sauvegarde globale sur les domaines atomiques, protection anti-perte, et persistance runtime uniquement après succès backend.

## Résultat produit vérifié

- Profil / Design / Performance partagent le bandeau `Modifications de la configuration non enregistrées` et l’action `Enregistrer la configuration`.
- Catalogue / Agenda / Sécurité / Équipe n’exposent plus de sauvegarde globale de profil.
- Un avertissement passif reste visible sur un onglet atomique lorsqu’une configuration staged reste non enregistrée.
- `beforeunload` protège fermeture/rechargement tant que `isDirty=true`.
- `updateProfile()` ne commit plus les préférences runtime immédiatement.
- `saveProfile()` commit thème/runtime uniquement après succès `PUT /clinics/me`; l’échec conserve `isDirty=true`.
- Le Read Truth `/clinics/me` continue de bloquer les surfaces profile-backed si la lecture backend échoue.
- Aucun endpoint métier ni schéma DB modifié.
- Aucun Vercel.

## Goal visuel / preuves

- BEFORE immuable : `2a6bfd8a10baddf770fed5e2ffbecc3f65f4468d`.
- AFTER produit : `e472ec47f411850f3270335fd92278c1c08b4fc5`.
- R1 cert #1 `32392304984` — SUCCESS.
- R1 cert final #2 `32393398276` — SUCCESS.
- Artifact final : `9415784766`.
- Digest : `sha256:329431c1aded9c5c5fd7f90f3c2c4a45ac0da13b837bd61be2075c175fc354ae`.
- 35 BEFORE + 35 AFTER : 7 onglets × 5 viewports (1440/1024/768/430/390).
- AFTER : 0 overflow horizontal, 0 erreur runtime.
- Score visuel : **9,5/10**.

## Compatibilité corrective

Le premier passage a révélé deux contrats historiques devenus obsolètes avec R1, sans défaut produit :

1. R2 #30 cherchait encore le bouton legacy `Mettre à jour le profil`, supprimé volontairement par R1.
2. CI frontend cherchait encore `profileBackedTabs` inline dans `SettingsContainer.tsx`, alors que R1 centralise cette doctrine dans `saveDoctrine.ts`.

Commit correctif `10ca5475279f579a841bbcce041ffcb7fb6b3f5e` : uniquement
- `.github/workflows/settings-profile-r2-visual-cert.yml`
- `frontend/src/features/admin/Settings/profileTeamReadTruth.test.ts`

Aucun fichier produit modifié entre `e472ec47...` et `10ca5475...`; l’évidence visuelle R1 reste donc strictement équivalente au HEAD final produit + harness.

## Gates finaux exact-head `10ca5475...`

- R1 #2 `32393398276` — SUCCESS.
- R2 #31 `32393398271` — SUCCESS — artifact `9415747239` — digest `sha256:852794c8b3f3c1047cffd96b3fa09286eeb114badadd381f09b5cfece5575bde`.
- CI #1491 `32393398293` — SUCCESS : frontend tests/build, backend tests & durcissement, garde production négative.
- T2 #722 `32393398320` — SUCCESS.
- RBAC #142 `32393398376` — SUCCESS.
- Branding #75 `32393398371` — SUCCESS.
- IA #25 `32393398297` — SUCCESS.
- Profile/Team Read Truth #19 `32393398296` — SUCCESS.
- R10 #7 `32393398260` — SUCCESS.
- Patient P7 Final #21 `32393398381` — SUCCESS.

## Dette non bloquante

Le bouton local historique de `ProfileTab.tsx` existe encore dans le markup mais est masqué par le shell R1. Il n’est plus exposé au produit. Nettoyage structurel possible ultérieurement sans bénéfice utilisateur immédiat.

## Conclusion

**R1 CERTIFIED — READY TO MERGE.**

La doctrine de sauvegarde affichée correspond désormais à la persistance réelle : staged pour Profil / Design / Performance, atomique ailleurs, protection anti-perte active, runtime committé uniquement après vérité backend.
