# T1 — surface certifiable actuelle

Date : 2026-09-13

## Verdict

Le Document Studio certifiable actuel couvre **P1→P6 uniquement** : Ordonnance, Certificat, Devis, Note Honoraires, Suivi Paiement et Document Libre.

Le Compagnon Diagnostique historique P7 reste volontairement hors du contrat produit actif. Son code dormant n'est pas revendiqué comme surface runtime certifiée.

## Preuves de périmètre

- `StudioTabs.tsx` expose uniquement P1→P6.
- `DocumentStudioVocabulary.ts` couvre les six pages documentaires actives.
- `DocumentTabNavigationPolicy.ts` couvre les états dirty des pages actives.
- le navigateur T2 contient un garde d'absence du Compagnon Diagnostique.
- commits historiques `a294dacc428d7bee43f910bcb3e71bd8bc6f3496` et `8e8bb2c245e5b742a37ac29d9b0b6a9aec9e4481` retirent explicitement P7 de la surface certifiable.

## Certification runtime observée

HEAD comportemental certifié avant closeout documentaire : `51e98dd3f14882278e7de5a2f862bb7a256d985b`.

T2 Runtime Browser Certification `#2645` / run `34750958888` : **success**.

Le job `T2 Browser Runtime Matrix` (`103707302825`) a exécuté avec succès :

- génération d'un credential jetable de certification ;
- seed du second patient synthétique `T2-0002` ;
- PDF runtime strict ;
- réconciliation persistée P3/P4/P5 ;
- matrice navigateur authentifiée P1→P6 ;
- probe transversal T1 ;
- probe P6 Document Libre ;
- impression navigateur et fraîcheur PDF ;
- upload des preuves.

### Boundary patient A→B

Le probe T1 a observé :

- patient A `T2-0001`, patient B `T2-0002` ;
- réponses A volontairement retardées puis libérées ;
- B reste autoritaire avant libération de A ;
- B reste autoritaire après libération de A ;
- aucune erreur de routage ;
- verdict : **PASS**.

### Navigation URL dirty

Le probe a observé :

- `Annuler` restaure l'URL du document courant ;
- le brouillon reste conservé ;
- la confirmation dirty est bien armée ;
- `Continuer` atteint la cible ;
- verdict : **PASS**.

### Frontière clinique

Le probe a observé :

- Compagnon Diagnostique absent ;
- aucune requête `ai-diagnostic` ;
- aucune page error ;
- verdict : **PASS**.

### Matrice P1→P6 et sorties

La matrice navigateur T2 a conclu `greenPages=6/6` et le stress de navigation a exécuté `10/10` transitions attendues avec dirty guard observé.

Le même run a également certifié :

- PDF runtime valide (`application/pdf`, signature `%PDF`) ;
- réconciliation P3/P4/P5 ;
- P6 sans overflow/clipping aux viewports 390×844, 768×1024, 1280×900 ;
- impression via PDF blob → iframe cachée → `print()` ;
- fraîcheur PDF prouvée par deux hashes distincts et observation du dernier payload.

Artefact : `t2-browser-evidence`, artifact ID `10316225660`, digest `sha256:886455c2ffcb560e50cb22e0e3798cc362459615904afec3da9c6396c2aaf333`.

## Gates complémentaires observés sur le même HEAD

- Catalog Connected Truth Certification `#1094` / run `34750958896` : **success**.
- Cabinet Upgrade PostgreSQL Certification `#160` / run `34750958994` : **success**.
- Patient P7 Final Certification `#1309` / run `34750959000` : **success** ; ce workflow ne réactive pas P7 dans le Document Studio.
- M6-I Biometric Passkey Certification `#1445` : **skipped** attendu.
- CI principal `#3701` / run `34750958892` : encore en cours au moment de ce closeout intermédiaire ; les jobs frontend/build déjà terminés sont verts, le job backend principal n'est pas encore terminal.

## Limites et closeout

Aucune modification UI/UX produit n'est incluse dans T1. Le changement de plafond du rate limiter est strictement limité au serveur runtime T2 jetable ; la politique produit reste inchangée.

T1 ne doit être déclaré fermé et mergé qu'après :

1. CI principale terminale verte ;
2. mise à jour documentaire finale ;
3. gates exact-head du HEAD documentaire final ;
4. merge squash exact-head ;
5. vérification post-merge sur `master`.
