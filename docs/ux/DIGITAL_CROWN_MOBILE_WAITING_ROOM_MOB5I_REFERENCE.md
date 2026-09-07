# DIGITAL CROWN — MOB-5I Salle d’attente — Référence UI

## Référence livrée

### Navigation
La Salle d’attente reste un accès secondaire dans `Plus` pour ne pas dégrader les accès principaux : Aujourd’hui, Patients, Actions rapides, Assistant.

Entrée : `Salle d’attente` + badge numérique uniquement si au moins un patient est en attente.

### Vue livrée
- compteur Salle d’attente ;
- liste dérivée de `Snapshot.appointments` ;
- ordre par heure de rendez-vous ;
- ticket affiché seulement s’il existe ;
- état vide explicite ;
- action principale `Au fauteuil` => `EN_COURS` / backend `EN_FAUTEUIL` ;
- touch targets >= 44 px ;
- aucun menu horizontal ;
- aucune durée d’attente inventée.

### Agenda
Les cartes Agenda affichent `En salle d’attente` et permettent `Planifié → En salle d’attente` via le sélecteur de statut existant.

### Données
- source unique : `Snapshot.appointments` ;
- filtre : `status === 'EN_ATTENTE'` ;
- `ticket_number` purement informatif ;
- aucune nouvelle collection métier locale.

## Anti-patterns refusés et évités
- dupliquer un rendez-vous dans une collection locale ;
- calculer `attente = now - datetime_start` ;
- remplacer l’Agenda par la Salle d’attente ;
- ajouter une 6e destination dans la bottom-nav ;
- exposer une action non autorisée côté serveur.

## Preuve de conformité
- AFTER run `34169388445` — SUCCESS ;
- artifact `10035225974` ;
- 390×844 / 430×932 / 768×1024 sans overflow ni erreur page/console ;
- compteur, ticket `#12`, CTA `Au fauteuil`, entrée `Plus` et badge présents ;
- score visuel **9.3/10** ;
- PR `#367` mergée au SHA `e2522a6d8b4794e64253eb4af36500e18cd87b40`.

Statut : `REFERENCE DELIVERED — CERTIFIED PRE-MERGE — PRODUCT MERGED`.
