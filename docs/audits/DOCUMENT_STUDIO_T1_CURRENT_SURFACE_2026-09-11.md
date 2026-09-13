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

## Certification runtime comportementale

HEAD comportemental historique : `51e98dd3f14882278e7de5a2f862bb7a256d985b`.

T2 Runtime Browser Certification `#2645` / run `34750958888` : **SUCCESS**.

Ce run a prouvé :

- isolation patient A/B avec réponses A retardées ;
- patient B autoritaire avant et après libération des réponses A ;
- navigation URL dirty `Annuler` / `Continuer` ;
- brouillon conservé après annulation ;
- Compagnon Diagnostique absent ;
- aucune requête `ai-diagnostic` ;
- matrice navigateur P1→P6 `greenPages=6/6` ;
- stress navigation `10/10` ;
- P6 sans overflow/clipping aux viewports 390×844, 768×1024 et 1280×900 ;
- PDF runtime strict ;
- impression navigateur ;
- fraîcheur PDF ;
- réconciliation P3/P4/P5.

Artefact historique : `t2-browser-evidence`, ID `10316225660`, digest `sha256:886455c2ffcb560e50cb22e0e3798cc362459615904afec3da9c6396c2aaf333`.

## Certification exact-head après réalignement master

La branche T1 a été réalignée avec `master` puis recertifiée sur :

HEAD : `2e5644a447c891e2a4772632aa14b3be32fbaadb`.

Gates observés sur ce HEAD :

- CI principal `#3707` / run `34751837897` : **SUCCESS** ;
- T2 Runtime Browser Certification `#2651` / run `34751838021` : **SUCCESS** ;
- Catalog Connected Truth `#1099` / run `34751837908` : **SUCCESS** ;
- Cabinet Upgrade PostgreSQL `#166` / run `34751837937` : **SUCCESS** ;
- Patient P7 Final `#1314` / run `34751837988` : **SUCCESS** ;
- M6-I `#1451` : **SKIPPED** attendu.

Le job T2 exact-head `T2 Browser Runtime Matrix` / `103709592150` a passé notamment :

- `Seed T1 second isolated patient` ;
- `Certify strict runtime PDF` ;
- `Certify P3 P4 P5 persisted reconciliation` ;
- `Execute authenticated browser matrix` ;
- `Certify T1 transversal runtime boundaries` ;
- `Certify P6 Document Libre editor` ;
- `Certify browser print and PDF freshness` ;
- `Upload browser evidence`.

Artefact exact-head : `t2-browser-evidence`, ID `10316051646`, digest `sha256:d0888b44cf7ba4a4413d4f66442aa808a631591a024cf5a6cbcc4e73c4de5b7f`.

## Limites

Aucune modification UI/UX produit n'est incluse dans T1. Le changement de plafond du rate limiter reste strictement limité au serveur runtime T2 jetable ; la politique produit reste inchangée.

Les validations humaines cliniques/réglementaires/production éventuelles restent distinctes de la fermeture engineering/runtime T1.

## Closeout

Engineering + runtime automatisé T1 sont fermés sur la surface active P1→P6 **pour le HEAD exact `2e5644a...`**, sous réserve du dernier HEAD documentaire de closeout qui doit encore repasser les gates avant merge.

Séquence finale : mise à jour documentaire canonique → gates exact-head du HEAD documentaire final → squash merge PR #465 → vérification post-merge `master`.
