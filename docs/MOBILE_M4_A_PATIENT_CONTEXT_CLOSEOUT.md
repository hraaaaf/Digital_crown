# Digital Crown — Mobile Full Experience — M4-A Patient contextuel — Closeout

Date : 2026-08-24
Status : CLOSED

## Goal

Depuis une fiche patient desktop, générer un pont QR opaque qui, après appairage/authentification mobile, ouvre exactement ce dossier patient sans exposer de PHI ni d’identifiant patient dans le QR ou l’URL mobile.

## Produit exact

- base : `12b7f758eaab69fcbcf500af0909cceea0abc124`
- HEAD produit : `a005c5d83757579c5b6e53a4bc288ebb6f0929b6`
- PR : #238
- merge : `4ad243013c2d999f014302252e5e2bb9f2184c29`
- structure PR : 1 commit / 12 fichiers / 0 behind
- CI : #1817 / run `32782329238`
- Vercel : aucun

## Résultat

- route mobile ID-less `/mobile/context` ;
- contexte ressource stocké côté serveur dans `mobile_bridge_contexts`, lié au pairing, au cabinet, à l’utilisateur cible puis au device ;
- token QR opaque `c.<secret>` ;
- self-target par défaut, ciblage collègue réservé admin même cabinet ;
- permission Patients, tenant, patient actif et device revalidés côté serveur ;
- contexte IndexedDB scoped cabinet + device et purgé avec la session ;
- frontend fail-closed si `resource_type != patient` ou `contains_patient_data != false` ;
- aucune donnée patient ni ID patient dans le QR ou l’URL mobile.

## BEFORE

Audit #1796 : SUCCESS.

- 5/5 captures inspectées ;
- 0 overflow horizontal ;
- 0 erreur runtime ;
- aucun bridge de ressource patient exact avant le lot.

## AFTER exact-head

Job `M4-A Patient contextual bridge AFTER` de CI #1817 : SUCCESS.

Artifact :
- id `9540282039`
- nom `mobile-m4a-patient-after`
- head SHA `a005c5d83757579c5b6e53a4bc288ebb6f0929b6`
- digest `sha256:f903425b1d157f4f4acd68b700c32408920a3853a14aa83ad729ebf463db4d94`

Gates visuels/runtime :
- 13/13 captures ;
- desktop : 768×1024 et 1280×900 ;
- mobile : 390×844, 430×932, 768×1024 ;
- 3/3 parcours E2E pairing → patient exact ;
- `safePairingBodies = true` ;
- route finale `/mobile/context` sans ID ni query ;
- 0 erreur runtime ;
- 0 overflow horizontal ;
- aucun contrôle M4-A <44 px.

Score visuel final : **9,5/10**.

## Preuve backend

CI #1817 : SUCCESS.

- backend : **2796 passed / 8 skipped / 0 failed** ;
- 4 warnings SQLAlchemy existants dans `superadmin.py`, non liés à M4-A ;
- frontend tests : SUCCESS ;
- frontend build : SUCCESS ;
- prod safety check : SUCCESS ;
- garde production négative : SUCCESS ;
- T2, Catalog, Patient P7, Patient Indicators, Patient Architecture, Security, Portability, Onboarding et Settings : SUCCESS sur le HEAD exact.

## Preuve QR

Le test backend capture le payload réel transmis au générateur QR avant encodage image et exige :

- path `/mobile/onboarding` ;
- seul query param `token` ;
- token égal au `ZKAPairingToken.token` ;
- token opaque préfixé `c.` ;
- aucun `patient_id`, nom patient ou numéro de dossier dans le payload.

## Isolation état test

Le fixture M4-A isole :
- `_license_cache` ;
- `backend.utils.rate_limit._store_path` vers un fichier `tmp_path` propre à chaque test.

Le runtime reste inchangé : `MAX_ATTEMPTS=5`, fenêtre 600 s, clé `scope + IP`.

## Post-merge

`master` vérifié sur `4ad243013c2d999f014302252e5e2bb9f2184c29`, avec `a005c5d83757579c5b6e53a4bc288ebb6f0929b6` comme parent produit.

## Conclusion

M4-A Patient contextuel est CLOSED. Prochain lot : M4-B Radio contextuelle.