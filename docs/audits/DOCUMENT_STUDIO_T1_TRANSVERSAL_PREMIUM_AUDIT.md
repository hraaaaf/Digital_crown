# Document Studio — T1 Audit transversal premium

Date : 2026-09-13
Scope canonique : **P1→P6 actifs uniquement**.
PR : #465 `test(t1): certify active P1-P6 transversal boundaries`.

## 1. Contrat de preuve

- **CODE VÉRIFIÉ** : démontré par source/diff.
- **TEST EXÉCUTÉ** : réellement exécuté avec résultat observé.
- **INTERACTION RUNTIME** : observée dans le navigateur authentifié.
- **CERTIFICATION** : uniquement après gates runtime/CI exact-head requis.

Le Compagnon Diagnostique historique P7 est hors de la surface Document Studio active. Son code dormant ne doit pas être mélangé à la certification T1 actuelle.

## 2. Frontières transversales certifiées

T1 couvre :

1. isolation patient A/B ;
2. résistance aux stale responses ;
3. navigation dirty manuelle et URL ;
4. frontière clinique avec absence du chemin `ai-diagnostic` depuis le Studio actif ;
5. vérité produit P1→P6 uniquement ;
6. réutilisation du T2 pour runtime, responsive, PDF et navigation.

## 3. Engineering vérifié

Les correctifs T1-A→T1-E restent la base :

- reset patient-scoped et remount au changement de patient ;
- fetches patient/suggestions cancellation-safe ;
- `DocumentTabNavigationPolicy` centralise les transitions dirty ;
- suppression des side-channels cliniques partagés non autoritatifs ;
- retrait du point d'entrée actif vers le Compagnon Diagnostique ;
- durcissement vérité UI, labels/ARIA/focus/Escape et shell responsive ;
- harness `scripts/certify_document_studio_t1.sh` limité à P1→P6 ;
- credential runtime T2 jetable ;
- plafond login augmenté uniquement dans le serveur T2 isolé, sans modification de la politique produit.

## 4. Preuve comportementale initiale

HEAD comportemental : `51e98dd3f14882278e7de5a2f862bb7a256d985b`.

T2 Runtime Browser Certification `#2645` / run `34750958888` : **SUCCESS**.

Le probe transversal a observé :

- B autoritaire avant libération des réponses A retardées : `true` ;
- B autoritaire après libération : `true` ;
- route errors : `[]` ;
- annulation URL dirty restaure l'URL : `true` ;
- brouillon conservé : `true` ;
- confirmation dirty atteint la cible : `true` ;
- Compagnon Diagnostique absent : `true` ;
- requêtes `ai-diagnostic` : `[]` ;
- page errors : `[]`.

Artefact historique : `t2-browser-evidence`, ID `10316225660`, digest `sha256:886455c2ffcb560e50cb22e0e3798cc362459615904afec3da9c6396c2aaf333`.

## 5. Réalignement master et recertification exact-head

La branche T1 a été réalignée avec le master `28ec7f531b1a3dbedd9180ddbf48c75b067c8aa5` via le commit de branche `2e5644a447c891e2a4772632aa14b3be32fbaadb`.

Sur ce HEAD exact :

- CI `#3707` / `34751837897` : **SUCCESS** ;
- T2 `#2651` / `34751838021` : **SUCCESS** ;
- Catalog Connected Truth `#1099` / `34751837908` : **SUCCESS** ;
- Cabinet Upgrade PostgreSQL `#166` / `34751837937` : **SUCCESS** ;
- Patient P7 Final `#1314` / `34751837988` : **SUCCESS** ;
- M6-I `#1451` : **SKIPPED** attendu.

Le job T2 exact-head `T2 Browser Runtime Matrix` / `103709592150` a terminé **SUCCESS** avec notamment :

- credential runtime jetable ;
- seed patient B ;
- PDF runtime strict ;
- réconciliation P3/P4/P5 ;
- matrice navigateur authentifiée ;
- probe transversal T1 ;
- probe P6 Document Libre ;
- impression navigateur et fraîcheur PDF ;
- upload des preuves.

Artefact exact-head : `t2-browser-evidence`, ID `10316051646`, digest `sha256:d0888b44cf7ba4a4413d4f66442aa808a631591a024cf5a6cbcc4e73c4de5b7f`.

## 6. Statut closeout

**Engineering T1 P1→P6 : fermé sur le HEAD exact `2e5644a...`.**

**Runtime transversal T1 : PASS observé sur ce même HEAD.**

**CI/T2 et gates voisins déclenchés : terminaux conformes sur ce même HEAD.**

P7 reste dormant et hors surface active ; le workflow Patient P7 Final ne constitue pas une réactivation produit.

Le présent commit documentaire crée volontairement un nouveau HEAD. Il doit donc être recertifié exact-head avant squash merge #465.

## 7. Hors périmètre engineering

- validation clinique/réglementaire humaine éventuelle ;
- certification sur cabinet réel / production locale réelle ;
- toute réactivation future de P7, qui exige un chantier produit + clinique séparé.

## 8. Séquence restante

1. aligner la roadmap canonique sur ce closeout ;
2. exécuter/observer les gates exact-head du HEAD documentaire final ;
3. vérifier mergeable + reviews/threads ;
4. squash merge #465 avec contrôle du HEAD attendu ;
5. vérifier `master` post-merge ;
6. poursuivre avec T2 uniquement après fermeture réelle de T1.
