# Catalogue connecté — Goal visuel et contrat métier

Statut : CERTIFIÉ — produit `f0238b8245b61430ca64714f74aa87a580c7d37a`

## Goal

Faire du catalogue cabinet R6 la source utilisée par les actes cliniques et le Master Plan, tout en figeant par valeur le nom/code/tarif au moment où un acte entre dans le plan.

## Succès observable

- `/actes/catalog/search?q=` conserve son contrat public mais lit uniquement le catalogue tenant du cabinet.
- `quick-add` écrit dans ce même catalogue tenant, plus dans le catalogue global legacy.
- Dans Clinique, un praticien recherche un acte par nom/code/spécialité, récupère nom + tarif, peut les modifier, puis l'ajoute au Master Plan.
- Le Master Plan conserve `act_id`, code, nom et prix capturés.
- Modifier ou désactiver ensuite l'acte dans Réglages ne modifie jamais le snapshot du plan existant.
- Une mise à jour de statut/date d'une étape historique reste possible après désactivation de l'acte.
- Un nouveau snapshot ne peut pas référencer un acte appartenant à un autre cabinet.

## BEFORE

SHA immuable : `e0be81e25833782a2cfc3ebddff68983d2624f9c`.

À ce SHA, `ClinicalHub.tsx` = blob `45d0c00031f7078dc260263b7c8c9a86615e56b9` et le Master Plan persiste uniquement `title / assistant / status / date_str`. Aucun sélecteur catalogue ni snapshot catalogue n'est affiché ou stocké.

Viewports certifiés : 1440x1200, 768x1200, 390x1200, 360x1200, 320x1200.

## Référence visuelle / wireframe avant implémentation

```text
┌ Ajouter un acte au plan                         [Tarif figé] ┐
│ Choisissez un acte du catalogue du cabinet.                  │
│ [ Rechercher nom, code ou spécialité… ]                      │
│                                                              │
│ Acte sélectionné                                             │
│ Nom retenu [ Détartrage complet          ]  Tarif [ 500 DH ] │
│                                      [ Ajouter au plan ]      │
└──────────────────────────────────────────────────────────────┘

Master Plan
  Détartrage complet
  Catalogue cabinet · Prévention · DET-001 · 500 DH · Tarif capturé
```

## Critères UX

- vocabulaire praticien, pas de jargon technique de persistance ;
- erreur catalogue fail-closed, sans faux actes de remplacement ;
- override nom/tarif explicite avant ajout ;
- mobile sans overflow horizontal ;
- aucun changement visuel dans le cœur clinique P7 hors ajout du bloc catalogue ;
- le badge visible est `Tarif figé`, pas `snapshot` ;
- labels du sélecteur explicitement associés à leurs inputs.

## Architecture de sécurité

Les implémentations P7 Clinique et Prescriptions sont déplacées sans modification dans des `*Core` byte-identiques. Les façades ne remplacent que les points d'intégration catalogue. La certification vérifie les SHA des deux cores.

Pour le Master Plan :
- nouveau snapshot : `act_id` validé contre `cabinet_catalog_acts` du tenant courant et acte actif ;
- nom/tarif : overrides autorisés puis copiés dans le snapshot ;
- code : recanonicalisé depuis l'acte tenant ;
- snapshot historique identique : réutilisé sans redéréférencer le catalogue mutable, afin qu'une désactivation ultérieure ne casse pas l'historique ;
- prix stocké en `NUMERIC(12,2)` ;
- révision du plan conserve également le snapshot JSON.

## Certification finale

Workflow `Catalog Connected Truth Certification` #8, run `32474152651` — SUCCESS.
Artifact `9443760454`.
Digest `sha256:09e14f0391143bf7faf28ce38f1ea84d034139dec32fc8b39313dae8c0973ca9`.

Preuves :
1. BEFORE exact recapturé sur 5 viewports ;
2. cores certifiés byte-identiques ;
3. tests backend ciblés verts ;
4. tests frontend ciblés + build verts ;
5. snapshot enregistré à 500 DH ;
6. catalogue modifié/désactivé à 650 DH ;
7. plan historique resté à 500 DH ;
8. mise à jour du statut historique réussie pendant désactivation ;
9. acte réactivé à 650 DH et sélecteur AFTER prérempli à 650 DH ;
10. AFTER 5/5 : overflow 0, page errors 0, HTTP 5xx 0.

Score visuel : **9,5/10**.

Gates exact HEAD produit `f0238b8245b61430ca64714f74aa87a580c7d37a` :
- Catalogue #8 `32474152651` — SUCCESS ;
- CI #1509 `32474152694` — SUCCESS ;
- T2 #734 `32474152628` — SUCCESS ;
- P7 #33 `32474152905` — SUCCESS.

Closeout détaillé : `docs/settings/CATALOG_CONNECTED_CLOSEOUT.md`.

Aucun Vercel.
