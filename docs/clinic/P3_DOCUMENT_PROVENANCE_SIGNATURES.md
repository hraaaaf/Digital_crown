# P3 — Documents, auteurs et signatures multi-praticiens

## Statut

Implémentation P3 mergée jusqu'à l'UI de signature. Le gate reproductible de préservation locale PR #463 est en cours de certification ; ce document ne déclare donc pas encore P3 totalement certifié.

## Goal

Ajouter une provenance clinique multi-praticiens explicite aux documents générés et une signature praticien applicative liée aux octets archivés, sans déplacer, réécrire ni remplacer le stockage documentaire local existant.

## Invariants locaux non négociables

- `DocumentArchive` et les fichiers locaux restent la source de vérité.
- `uploaded_by_id` reste l'acteur technique authentifié.
- l'auteur clinique est un `User.id` existant, distinct de l'acteur technique si nécessaire.
- les documents historiques ne sont jamais réattribués automatiquement : provenance inconnue = `NULL`.
- aucune migration destructive, aucun backfill forcé et aucune dépendance cloud documentaire.
- les relations vers `users.id` sont nullable et `ON DELETE SET NULL`.
- remplacer/régénérer les octets d'un document invalide toute provenance de signature antérieure.

## Architecture mergée

### Auteur clinique

Champs additifs sur `DocumentArchive` :

- `author_practitioner_id` ;
- `signed_by_practitioner_id` ;
- `signed_at`.

La résolution de l'auteur est fail-closed :

- praticien assignable = même cabinet, actif, approuvé ;
- dentiste salarié autorisé ;
- propriétaire actif autorisé s'il est dentiste/admin ;
- secrétaire ou autre acteur non-praticien doit sélectionner explicitement un auteur clinique valide ;
- aucun auteur propriétaire n'est inventé silencieusement.

Le contexte auteur pilote l'identité visible du PDF généré et l'attribution praticien des actes générés depuis Honoraires, tandis que l'acteur authentifié reste conservé pour l'audit technique.

### Signature praticien

La signature P3 est une **provenance de signature praticien au niveau applicatif Digital Crown**, liée au SHA-256 et à la taille persistés du fichier archivé.

Elle **n'est pas** une signature électronique qualifiée, une signature PKI ni une signature numérique adossée à un certificat.

Avant enregistrement :

- document canonique `ACTIF` ;
- auteur P3 présent ;
- utilisateur connecté = auteur exact ;
- praticien actif/approuvé et assignable ;
- fichier physique présent ;
- SHA-256 physique = SHA-256 persisté ;
- taille physique = taille persistée lorsqu'elle est renseignée.

Le même auteur peut réappeler la signature de façon idempotente sans déplacer le timestamp initial. Un fichier absent, altéré, un auteur inconnu, un signataire différent ou un état non actif est refusé.

### Vérification publique

Le legacy `/verify/{doc_id}` qui présentait tout document trouvé comme `Authentique & Signé` a été remplacé pour ce chemin canonique.

États désormais distingués :

- `Intégrité vérifiée • Signature praticien enregistrée` ;
- `Intégrité vérifiée • Non signé` ;
- `Intégrité non vérifiée` ;
- `Signature incohérente` ;
- document non actif/invalide.

Le wording public rappelle explicitement la limite de portée de la signature applicative.

## Permissions

Aucune permission supplémentaire `sign_documents` n'a été créée.

La signature cumule déjà des contraintes plus strictes :

1. permission existante du type de document ;
2. type non mappé => refus fail-closed ;
3. utilisateur = auteur exact ;
4. praticien même cabinet, actif et approuvé ;
5. intégrité du fichier exacte.

Cette combinaison évite une seconde permission redondante susceptible de produire des configurations contradictoires.

## UX certifiée avant closeout final

### Document Studio

Un sélecteur `Auteur clinique` est intégré au header du Studio.

Préselection sûre :

1. praticien authentifié s'il est éligible ;
2. référent clinique du patient ;
3. praticien unique du cabinet ;
4. sinon aucune sélection silencieuse.

Seul le POST `/documents/generate` reçoit `author_practitioner_id`.

### Archives patient

Chaque document canonique expose un état véridique :

- `Non signé` + auteur enregistré ;
- `Signature praticien enregistrée` + signataire + timestamp ;
- `Provenance historique non attribuée` lorsqu'aucun auteur P3 n'existe.

L'action `Enregistrer ma signature` n'est visible que pour l'auteur connecté, sur un document canonique existant et non signé. Le backend reste l'autorité fail-closed.

Le menu d'actions est contenu à 390x844 et 1366x700 ; la cible tactile de signature mobile est >=44 px.

## Preuves GitHub vérifiées

### Provenance backend

- PR #454 mergée.
- HEAD final PR : `5bf4fa0835007d774312a49ce77235fffa1c309f`.
- merge : `04304b7f5428d3c684e54a7de71d76d135b6a3aa`.

### Auteur clinique UI

- PR #455 mergée.
- HEAD : `de9819eb4af4d41feb220dacb2e00669b5bc6be0`.
- merge : `3fc3b0ac604b6a291000dc7c91915cb377713788`.
- certification visuelle finale : 390x844 / 768x1024 / 1280x900, 0 overflow, 0 runtime error, score 10.0/10.

### Signature backend

- PR #457 mergée.
- HEAD : `ca191f27085ce28f3072b276701500717708d049`.
- merge : `3b3152813b635393c880c8eb270772060e85e1f6`.
- tests dédiés : intégrité, auteur-signataire exact, idempotence, permissions fail-closed, lecture publique fail-closed, conservation des octets physiques.

### Signature UI

- PR #459 mergée avec garde SHA.
- HEAD certifié : `3e0ca1f08ebbc5f19c28ac2e715cdf4e08480472`.
- merge : `a213376114ca26cedfdb7a112f9320156cf88adb`.
- P3 Signature UI `34727387320` : success, score **10.0/10**.
- Document History Actions AFTER `34727387326` : success à 390x844 et 1366x700.
- PostgreSQL `34727387310` : success.
- T2 `34727387337` : success.
- P2 Visual `34727387366` : success.
- CI `34727387334` : success.
- Patient P7 `34727387347` : success.

## Préservation des données

Le gate cabinet réel antérieur reste la preuve sur copie fraîche de données réelles :

- Patients 293 → 293 ;
- Documents DB 395 → 395 ;
- relations patient-document inchangées ;
- médias 2 642 fichiers / 353 518 486 octets inchangés ;
- hashes critiques inchangés ;
- actes 281 → 281 ;
- paiements 212 → 212.

P3 ajoute un gate isolé reproductible PR #463 afin de vérifier spécifiquement :

- self-migration provenance idempotente ;
- aucun backfill auteur/signataire/timestamp historique ;
- conservation id/patient/path/hash/taille/statut ;
- signature = métadonnées seulement, sans réécriture du fichier ;
- même contrat de migration exécuté sur SQLite isolé et PostgreSQL 18 isolé.

**Limite de preuve :** le gate #463 utilise un vault synthétique isolé + PostgreSQL 18 isolé ; il ne doit jamais être présenté comme une nouvelle copie de données patient réelles. Son verdict final sera ajouté ici après CI et merge.

## Ressources physiques

Salles/fauteuils sont **différés**. L'audit P3 n'a pas démontré de conflit de workflow clinique nécessitant ce modèle maintenant. Aucun schéma ni écran spéculatif n'est ajouté uniquement pour satisfaire une ligne de roadmap.

## Hors périmètre

- signature électronique qualifiée / PKI / certificat ;
- multi-site ;
- ressources physiques sans besoin workflow démontré ;
- déplacement vers un stockage cloud ;
- déploiement Vercel.

## Next exact

Certifier puis merger PR #463. Ensuite seulement : marquer P3 `CERTIFIÉ / MERGÉ`, mettre à jour le roadmap et fermer ce lot sans inventer de P4.
