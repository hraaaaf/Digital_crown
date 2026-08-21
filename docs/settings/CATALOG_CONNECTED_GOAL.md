# Catalogue connecté — Goal visuel et contrat métier

Statut : PREPARED — non certifié

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

La certification PR doit recapturer ce BEFORE dans le même run que l'AFTER aux viewports : 1440x1200, 768x1200, 390x1200, 360x1200, 320x1200.

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
- le badge visible est `Tarif figé`, pas `snapshot`.

## Architecture de sécurité

Les implémentations P7 Clinique et Prescriptions sont déplacées sans modification dans des `*Core` byte-identiques. Les façades ne remplacent que les points d'intégration catalogue. Le run vérifie les SHA des deux cores.

Pour le Master Plan :
- nouveau snapshot : `act_id` validé contre `cabinet_catalog_acts` du tenant courant et acte actif ;
- nom/tarif : overrides autorisés puis copiés dans le snapshot ;
- code : recanonicalisé depuis l'acte tenant ;
- snapshot historique identique : réutilisé sans redéréférencer le catalogue mutable, afin qu'une désactivation ultérieure ne casse pas l'historique ;
- prix stocké en `NUMERIC(12,2)` ;
- révision du plan conserve également le snapshot JSON.

## Preuve attendue

Workflow `Catalog Connected Truth Certification` :
1. checkout BEFORE exact ;
2. captures BEFORE 5 viewports ;
3. checkout PR HEAD exact ;
4. preuve byte-identique des cores ;
5. tests ciblés backend/frontend + build ;
6. enregistre un snapshot à 500 DH ;
7. modifie/désactive le catalogue à 650 DH ;
8. prouve que le plan reste à 500 DH et qu'un changement de statut fonctionne ;
9. réactive l'acte à 650 DH et prouve que le nouveau sélecteur propose 650 DH ;
10. captures AFTER sur les mêmes 5 viewports + contrôle overflow/page errors/HTTP 5xx.
