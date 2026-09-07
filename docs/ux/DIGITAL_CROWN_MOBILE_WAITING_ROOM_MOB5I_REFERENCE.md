# DIGITAL CROWN — MOB-5I Salle d’attente — Référence UI

## Référence verrouillée

### Navigation
La Salle d’attente reste un accès secondaire dans `Plus` pour ne pas dégrader les 4 accès principaux actuels : Aujourd’hui, Patients, Actions rapides, Assistant.

Entrée :
`Salle d’attente` + icône utilisateurs/horloge + badge numérique uniquement si au moins un patient est en attente.

### Vue
```text
Salle d’attente                         [3]
Patients actuellement présents

┌──────────────────────────────────────┐
│ #12   09:30   Sara El Mansouri      │
│       Contrôle                      │
│                         [Au fauteuil]│
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│       10:00   Youssef Amrani        │
│       Consultation                  │
│                         [Au fauteuil]│
└──────────────────────────────────────┘
```

Règles :
- ordre par heure de rendez-vous ;
- ticket affiché seulement s’il existe ;
- aucune durée d’attente inventée ;
- état vide explicite `Aucun patient en salle d’attente` ;
- action principale `Au fauteuil` => `EN_COURS` / backend `EN_FAUTEUIL` ;
- retour vers planifié disponible comme action secondaire uniquement si le composant d’action existant permet une transition claire sans ambiguïté ;
- touch targets >= 44 px ;
- aucun menu horizontal.

### Agenda
Les cartes Agenda doivent pouvoir afficher le nouvel état `En salle d’attente` et permettre la transition `Planifié → En salle d’attente` via le sélecteur de statut existant.

### Données
Source unique : `Snapshot.appointments`.
Filtre Salle d’attente : `status === 'EN_ATTENTE'`.
`ticket_number` est purement informatif.

## Anti-patterns refusés
- dupliquer un rendez-vous dans une collection locale de file d’attente ;
- calculer `attente = now - datetime_start` ;
- remplacer l’Agenda par la Salle d’attente ;
- ajouter une 6e destination dans la bottom-nav ;
- exposer une action non autorisée côté serveur.

Statut : `REFERENCE LOCKED — BEFORE RUNNING`.
