# DIGITAL CROWN — MOB-5I Salle d’attente — Proof

## Goal
Rendre la salle d’attente exploitable sur mobile depuis le modèle `Appointment` canonique, sans duplication métier ni métrique inventée.

## BEFORE — VERIFIED
- baseline : `fd19dab006d46f274946fd932927b9ac4821d3ec` ;
- run `34168710412` — SUCCESS ;
- artifact `10035019049` ;
- digest `sha256:add8126ca80cc347365732da80a766549840fe16cadafc572e424aff0c479873` ;
- 390×844 / 430×932 / 768×1024 : HTTP 200, 0 page error, 0 console error, 0 overflow ;
- aucune surface Salle d’attente dédiée.

## AFTER — VERIFIED
- run `34169388445` — SUCCESS ;
- product cert HEAD `11421e20913c90517cee5da7d7f2414ac2311e3d` ;
- artifact `10035225974` ;
- digest `sha256:efa961010bb3c1d189f8447c99a70d5dfaf42c893f49fd8a4db558b5dbccbd50` ;
- backend contract SUCCESS ; frontend contract SUCCESS ; frontend build SUCCESS ;
- 390×844 / 430×932 / 768×1024 : HTTP 200, 0 page error, 0 console error, 0 overflow ;
- compteur, patient, ticket `#12`, CTA `Au fauteuil`, entrée `Plus` et badge présents ;
- score visuel **9.3/10**.

## Produit / merge
- PR `#367` ;
- HEAD final `d6a234a24fbc3a64a69763688322de31fa38f7ba` ;
- CI PR `34169598948` — SUCCESS ;
- merge exact `e2522a6d8b4794e64253eb4af36500e18cd87b40` ;
- post-merge master `34170398551` — SUCCESS : backend tests, frontend tests/build et garde production verts.

## Closeout documentaire
- PR `#369` ;
- CI `34170522549` — SUCCESS ;
- T2 `34170522692` — SUCCESS ;
- aucun Vercel.

Statut : `DONE / MERGED / CLOSED`.
