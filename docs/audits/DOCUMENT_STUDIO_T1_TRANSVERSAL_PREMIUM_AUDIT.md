# Document Studio — T1 Audit transversal premium

Date : 2026-09-13
Scope canonique : **P1→P6 actifs uniquement**.
PR courante : #465 `test(t1): certify active P1-P6 transversal boundaries`.

## 1. Contrat de preuve

- **CODE VÉRIFIÉ** : démontré par source/diff.
- **TEST EXÉCUTÉ** : réellement exécuté avec résultat observé.
- **INTERACTION RUNTIME** : observée dans le navigateur authentifié.
- **CERTIFICATION** : uniquement après gates runtime/CI exact-head requis.

Le Compagnon Diagnostique historique P7 est hors de la surface Document Studio active. Son code dormant ne doit pas être mélangé à la certification T1 actuelle.

## 2. Risques transversaux ciblés

T1 ferme les frontières partagées suivantes :

1. isolation patient : aucun état patient A ne doit devenir autoritaire chez B ;
2. stale response : une réponse A tardive ne doit pas écraser B ;
3. navigation dirty : transitions manuelles et URL doivent respecter le même garde ;
4. frontière clinique : aucune exécution du chemin `ai-diagnostic` historique depuis le Studio actif ;
5. vérité produit : uniquement six pages P1→P6 ;
6. responsive/a11y/runtime : réutilisation du T2 complet plutôt que duplication de couverture.

## 3. Engineering vérifié

Les correctifs historiques T1-A→T1-E restent la base engineering :

- reset patient-scoped et remount au changement de patient ;
- fetches patient/suggestions cancellation-safe ;
- `DocumentTabNavigationPolicy` centralise les transitions dirty ;
- suppression des side-channels cliniques partagés non autoritatifs ;
- retrait du point d'entrée actif vers le Compagnon Diagnostique ;
- durcissement vérité UI, labels/ARIA/focus/Escape et shell responsive.

Le harness actuel `scripts/certify_document_studio_t1.sh` cible P1→P6 et exclut le test P7 dormant de la régression ciblée.

## 4. Certification runtime exécutée

HEAD comportemental certifié avant closeout documentaire : `51e98dd3f14882278e7de5a2f862bb7a256d985b`.

T2 Runtime Browser Certification `#2645` / run `34750958888` : **SUCCESS**.
Job : `T2 Browser Runtime Matrix` / `103707302825` : **SUCCESS**.

### Patient boundary

Le probe `frontend/scripts/certify-t1-transversal.mjs` a observé :

- A = `T2-0001`, B = `T2-0002` ;
- deux réponses A retardées puis libérées ;
- B autoritaire avant libération : `true` ;
- B autoritaire après libération : `true` ;
- route errors : `[]` ;
- verdict : **PASS**.

### URL dirty boundary

Observé :

- annulation restaure l'URL : `true` ;
- brouillon conservé : `true` ;
- confirmation dirty armée : `true` ;
- confirmation atteint la cible : `true` ;
- session de confirmation isolée : `true` ;
- verdict : **PASS**.

### Clinical boundary

Observé :

- Compagnon Diagnostique absent : `true` ;
- requêtes `ai-diagnostic` : `[]` ;
- page errors : `[]` ;
- verdict : **PASS**.

## 5. Couverture T2 réutilisée

Le même run T2 a passé :

- credential runtime jetable ;
- seed du patient B ;
- PDF runtime strict ;
- réconciliation P3/P4/P5 ;
- matrice navigateur P1→P6 ;
- stress navigation 10/10 transitions ;
- P6 390×844 / 768×1024 / 1280×900 sans overflow ni clipping ;
- impression navigateur ;
- fraîcheur PDF ;
- upload des preuves.

Artefact : `t2-browser-evidence`, ID `10316225660`, digest `sha256:886455c2ffcb560e50cb22e0e3798cc362459615904afec3da9c6396c2aaf333`.

## 6. Gates voisins observés

Sur le même HEAD comportemental :

- Catalog Connected Truth `#1094` / `34750958896` : **SUCCESS** ;
- Cabinet Upgrade PostgreSQL `#160` / `34750958994` : **SUCCESS** ;
- Patient P7 Final `#1309` / `34750959000` : **SUCCESS**, sans réactivation P7 dans Document Studio ;
- M6-I `#1445` : **SKIPPED** attendu.

CI principale `#3701` / `34750958892` était encore en cours au moment de cette mise à jour. Les jobs frontend/tests/build et les bridges M4 déjà terminés sont verts ; le job backend principal doit encore devenir terminal vert avant fermeture T1.

## 7. Correctifs d'infrastructure de certification

Le runtime T2 utilise désormais un credential jetable généré par workflow. Les probes historiques encore dépendants de l'ancien marqueur sont réalignés à l'exécution.

Le rate limiter produit reste inchangé. Le serveur **T2 isolé uniquement** élève son plafond de tentatives afin que les multiples probes authentifiés du même run ne s'auto-bloquent pas.

## 8. Statut actuel

**Engineering : convergé sur P1→P6.**

**Runtime transversal T1 : PASS observé.**

**T2 global : SUCCESS observé.**

**CI principale : encore non terminale au moment de ce document.**

T1 n'est donc pas encore déclaré fermé/mergé dans ce fichier. La fermeture finale exige : CI terminale verte → closeout documentaire cohérent → gates exact-head du HEAD documentaire final → squash merge exact-head → vérification post-merge `master`.
