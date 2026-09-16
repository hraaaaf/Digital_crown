# Mutuelles dentaires — CNOPS gate

Date: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branche: `feature/mutuelles-cnops-20260916`
PR: `#534`

## Goal

Integrer CNOPS dans le moteur Mutuelles existant, sans moteur parallele et sans regression CNSS:

`Honoraires -> Preparer CNOPS -> revue praticien -> validation -> PDF CNOPS hash-bound -> DocumentArchive`

## Succes observable

- binaire CNOPS exact identifie et valide par le cabinet;
- trust limite a `CABINET_VALIDATED_BINARY` pour ce SHA uniquement;
- preparation/validation/finalisation CNOPS via le moteur commun;
- politique administrative fail-closed;
- overlay lie a `organization + template_version + template_hash` exacts;
- aucune signature/cachet/decision assureur fabrique;
- UI de revue praticien executee en vrai runtime React/Chromium;
- non-regression CNSS couverte;
- branche reconstruite au-dessus du master courant sans supprimer de fonctionnalite hors CNOPS.

## Binaire CNOPS cabinet valide — ACQUIS

Le praticien/cabinet a explicitement valide le 2026-09-16 le binaire inspecte comme formulaire CNOPS dentaire utilise/acceptable au cabinet.

Identite immuable:

- fichier inspecte: `Feuile de soins denatires CNOPS - ATARBAWI.COM.pdf`;
- taille: `1 325 493` octets;
- pages: `2`;
- format: A4 paysage, `841.89 x 595.276 pt`;
- champs PDF: aucun;
- JavaScript: non;
- SHA-256: `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`;
- provenance d'acquisition: copie secondaire;
- validation humaine: cabinet/praticien, explicite, 2026-09-16;
- trust runtime autorise pour CE binaire exact: `CABINET_VALIDATED_BINARY`;
- template version: `CNOPS-DENTAL-CABINET-2026-09-16`.

Cette validation ne transforme pas la provenance en `OFFICIAL_PRIMARY`. Toute autre sequence d'octets doit repasser le gate hash/validation.

## Implementation — ACQUISE SUR LE CODE DU LOT

### Moteur commun

CNOPS reutilise les briques existantes:

- `InsuranceSubmissionDraft`;
- Honoraires comme source financiere;
- coherence serveur Honoraires/Acte;
- resolution NGAP sans fuzzy matching;
- source store local immuable;
- validation praticien;
- revalidation anti-stale;
- renderer PDF overlay hash-bound;
- hash du PDF final;
- archivage `DocumentArchive`.

Le facade commun supporte maintenant CNSS et CNOPS via les memes endpoints prepare/validate/finalize.

### Politique administrative CNOPS

Les donnees assure/beneficiaire sont explicites et fail-closed. Sont notamment modelises:

- nature de demande;
- nom assure;
- affiliation;
- immatriculation;
- CIN assure;
- adresse assure;
- lien avec assure si applicable;
- beneficiaire: identite, naissance, CIN, sexe;
- INPE praticien;
- type de soins;
- entente prealable si applicable;
- accident si applicable.

Aucune affiliation, immatriculation, identite, relation assure-beneficiaire ou donnee praticien inconnue n'est deduite silencieusement.

### Profil overlay CNOPS

Fichier canonique: `backend/services/insurance_cnops_dental_profile.py`.

- template SHA-256: `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`;
- template version: `CNOPS-DENTAL-CABINET-2026-09-16`;
- profile version: `cnops-dental-cabinet-2026-09-16-89097cac-v1`;
- capacite: 9 lignes d'actes;
- page 1: donnees administratives/praticien autorisees;
- page 2: dents, code NGAP, date, coefficient, montant;
- colonne valeur-cle volontairement non remplie faute de source fiable;
- aucune coordonnee signature/cachet/mutuelle/agent/decision assureur.

### UI praticien

Composant reel: `frontend/src/features/patients/CnopsInsuranceSubmissionReview.tsx`.

Le flow partage expose `Preparer CNOPS`, la revue praticien, la validation et la finalisation sans casser l'action CNSS existante.

## Invariants fail-closed — VERROUILLES

- aucune donnee administrative inconnue inventee;
- aucun lien assure-beneficiaire infere silencieusement;
- aucun INPE/IF/ICE deduit depuis un champ non explicitement identifie;
- aucune signature, aucun cachet, aucune decision assureur ou agent generes;
- le trust `CABINET_VALIDATED_BINARY` vaut uniquement pour le SHA exact;
- le profil overlay est lie au triplet organisation/version/hash exact;
- toute divergence Honoraires/Acte/NGAP/template apres validation invalide la finalisation;
- CNSS reste dans le meme moteur et doit rester non-regresse.

## Preuve UI deja acquise

Une certification runtime reelle a ete executee sur le composant React CNOPS sous Chromium, avec donnees deterministes de test:

- ancien HEAD certifie: `2acc3b1214219dc57897eb7388cda4065da2fb43`;
- workflow: `Mutuelles CNOPS Visual Certification`;
- run `#1` / id `35100939954`: `SUCCESS`;
- viewports: `390x844`, `768x1024`, `1280x900`;
- `overflowPx: 0` et aucune erreur runtime sur la preuve inspectee;
- validation visuelle humaine explicite acquise dans la conversation le 2026-09-16.

Cette preuve valide le design/flow implemente; elle ne remplace pas la recertification du HEAD final apres rebase/closeout.

## Rebase non-regressif — PREUVE STRUCTURELLE ACQUISE

Pour eviter de reintroduire un ancien arbre et de supprimer des travaux recents, le lot CNOPS a ete reconstruit depuis le master courant en reappliquant uniquement ses fichiers CNOPS/assurance.

Base verifiee au moment de la reconstruction:

- `master@63d3902656d0525dccac60cbc15cf2aa21b1ffd9`;
- tree master `af33ffcf33fb9d561e6e9cb42cf156d9ec4d7586`.

Commit d'implementation reconstruit avant closeout documentaire:

- `70bcff19086f691df224ba4ca47512743027b6f6`;
- comparaison master -> implementation: `ahead_by=1`, `behind_by=0`;
- exactement `21` fichiers modifies;
- tous appartiennent au perimetre CNOPS/assurance;
- aucun fichier Agenda, Cephalo ou Patient Companion retire/modifie par ce rebase.

Une branche de sauvegarde conserve l'ancien HEAD certifie: `backup/mutuelles-cnops-pre-rebase-20260916`.

## Certification finale

Au moment de ce closeout documentaire, les workflows du commit d'implementation `70bcff19...` ont ete declenches. Leur etat intermediaire n'est pas une preuve finale. Le HEAD documentaire final doit etre recertifie avant passage de la PR en ready/merge.

## Interdits maintenus

- second moteur Mutuelles/Honoraires;
- fuzzy mapping NGAP;
- backfill artificiel;
- promotion silencieuse d'une source secondaire en `OFFICIAL_PRIMARY`;
- signature/cachet/accord assureur fabrique;
- mutation de production;
- deploiement Vercel sans autorisation explicite;
- merge sans accord explicite utilisateur.

## Next exact

1. certifier le HEAD final apres ce closeout documentaire;
2. verifier CNOPS Visual + CI + non-regressions pertinentes;
3. verifier PR #534 mergeable et sans divergence master;
4. passer la PR en ready uniquement si tout est vert;
5. merger seulement apres accord explicite utilisateur;
6. verifier post-merge puis ouvrir le lot FAR separement.
