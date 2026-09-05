# Digital Crown — MOB-5 — Mobile secondaire à forte valeur

Status: AUDIT IN PROGRESS
Lot: MOB-5
Baseline master: `df48ef3cf1af8e9075828b3bf0b9b1f2c874fcda`

## Goal

Ne porter en mobile que les scénarios secondaires qui sont réellement fréquents, courts et plus efficaces que leur équivalent desktop.

## Gate de sélection

Un candidat MOB-5 n'est retenu que si :
1. scénario mobile réel et fréquent ;
2. action utile en moins de 30 secondes ;
3. meilleur au fauteuil / debout / hors poste que desktop ;
4. pas de duplication d'un flow déjà couvert par Aujourd'hui / Patients / + / Assistant / Plus ;
5. sécurité, permissions, offline et contexte patient préservés ;
6. bénéfice observable supérieur au coût de complexité.

## Candidats à auditer

- Bibliothèque clinique ;
- demandes RDV / Frontdesk ;
- aperçu multi-praticien ;
- Marketplace utilisateur.

## Verdict

À déterminer à partir du code et des parcours existants. Aucun écran produit ne doit être ajouté avant cette sélection.
