# R7 — Horaires & Agenda : Goal visuel et métier

Date : 2026-08-19
Scope principal : **Réglages → Horaires & Agenda**
Scope downstream autorisé uniquement lorsqu'il est nécessaire pour rendre un réglage vrai dans l'Agenda.

## Goal

Transformer l'écran actuel, partiellement décoratif, en configuration réellement appliquée :
- semaine d'ouverture persistée jour par jour ;
- jours fermés explicites ;
- fermetures exceptionnelles / congés administrables ;
- Agenda Jour/Semaine borné par les horaires réellement configurés ;
- suppression de l'UI des options sans comportement réel.

## BEFORE Settings certifiée

Workflow : `Settings Agenda R7 Visual Certification` #1
Run : `32206789386`
HEAD : `2044f20a3682dd3f559dd0162b6f17fdb92a2d21`
Artifact : `9349497163`
Digest : `sha256:ca60124495271392c7c135d2ee27d8b5bb5706f3cb5be2626ca010645737833a`
Viewports : 1440 / 1024 / 768 / 430 / 390 × 1200.

Constats visuels :
- desktop propre mais trois gros blocs donnent un poids visuel égal à des fonctions qui n'ont pas la même réalité ;
- mobile lisible mais très long ;
- `Mode d'Agenda` et `File d'attente (Tickets)` occupent environ la moitié de la surface utile alors que leur downstream est absent/incomplet.

## Audit downstream vérifié

### Horaires
- `CabinetSettings` persiste seulement un horaire global matin/après-midi et `is_continuous` ;
- aucune structure hebdomadaire n'existe aujourd'hui ;
- DailyView et WeeklyView affichent actuellement une grille codée en dur 08:00–19:00 ;
- le backend possède déjà `AgendaException` + GET/POST/DELETE `/agenda/exceptions`.

### `agenda_mode`
- stocké dans `CabinetSettings` ;
- non consommé par AgendaStudio, DailyView ou WeeklyView ;
- la flexibilité réelle est déjà portée par `Appointment.scheduling_type` (`EXACT_TIME`, `MORNING`, `AFTERNOON`, `FULL_DAY`) et choisie lors de la création du rendez-vous.

Verdict : **RETIRER DU PANNEAU SETTINGS**, garder le champ legacy en compatibilité tant qu'une migration de cleanup n'est pas justifiée.

### `use_tickets`
- stocké dans `CabinetSettings` ;
- affiche `Nouveau Ticket` dans AgendaStudio ;
- ce bouton n'a actuellement aucun `onClick` ;
- aucun routeur Ticket dédié n'a été trouvé dans la liste backend inspectée ; `Appointment.ticket_number` reste un champ de compatibilité.

Verdict : **RETIRER DE L'UI ACTIVE** tant qu'une vraie feature de file d'attente n'existe pas. Ne pas supprimer les colonnes DB dans R7.

## Modèle persistant cible

Ajouter de façon additive un `weekly_schedule_json` optionnel à `CabinetSettings`.

Format canonique :

```json
{
  "monday":    {"is_open": true,  "is_continuous": false, "morning_start": "09:00", "morning_end": "13:00", "afternoon_start": "14:00", "afternoon_end": "18:00"},
  "tuesday":   {"is_open": true,  "is_continuous": false, "morning_start": "09:00", "morning_end": "13:00", "afternoon_start": "14:00", "afternoon_end": "18:00"},
  "wednesday": {"is_open": true,  "is_continuous": false, "morning_start": "09:00", "morning_end": "13:00", "afternoon_start": "14:00", "afternoon_end": "18:00"},
  "thursday":  {"is_open": true,  "is_continuous": false, "morning_start": "09:00", "morning_end": "13:00", "afternoon_start": "14:00", "afternoon_end": "18:00"},
  "friday":    {"is_open": true,  "is_continuous": false, "morning_start": "09:00", "morning_end": "13:00", "afternoon_start": "14:00", "afternoon_end": "18:00"},
  "saturday":  {"is_open": true,  "is_continuous": false, "morning_start": "09:00", "morning_end": "13:00", "afternoon_start": "14:00", "afternoon_end": "18:00"},
  "sunday":    {"is_open": true,  "is_continuous": false, "morning_start": "09:00", "morning_end": "13:00", "afternoon_start": "14:00", "afternoon_end": "18:00"}
}
```

Compatibilité : si `weekly_schedule_json` est absent/null sur une ancienne installation, dériver les 7 jours de l'horaire global existant afin de **préserver exactement le comportement historique**, sans inventer un dimanche fermé ou un samedi ouvert.

L'écriture de la nouvelle semaine devient la nouvelle source de vérité. Les anciens champs globaux restent lisibles pendant la transition.

## Wireframe Settings cible

```text
Horaires & Agenda
Définissez les heures réellement utilisées par l'agenda et vos fermetures.

┌ Semaine d'ouverture ────────────────────────────────────────────┐
│ Lundi      [Ouvert ●]  09:00 → 13:00 | 14:00 → 18:00 [Pause] │
│ Mardi      [Ouvert ●]  09:00 → 13:00 | 14:00 → 18:00 [Pause] │
│ Mercredi   [Ouvert ●]  09:00 → 13:00 | 14:00 → 18:00 [Pause] │
│ Jeudi      [Ouvert ●]  09:00 → 13:00 | 14:00 → 18:00 [Pause] │
│ Vendredi   [Ouvert ●]  09:00 → 13:00 | 14:00 → 18:00 [Pause] │
│ Samedi     [Ouvert ●]  09:00 → 13:00 | 14:00 → 18:00 [Pause] │
│ Dimanche   [Fermé ○]                                             │
└─────────────────────────────────────────────────────────────────┘

┌ Fermetures & exceptions ────────────────────────────────────────┐
│ 22–29 août · Congés annuels                         [Retirer]   │
│ 06 novembre · Jour férié                           [Retirer]   │
│                                      [+ Ajouter une fermeture]  │
└─────────────────────────────────────────────────────────────────┘

                                             [Enregistrer]
```

Le wireframe montre une semaine de démonstration, **pas un défaut métier imposé** : les anciennes installations sont initialisées à partir de leur horaire global existant.

### Mobile

Chaque jour devient une carte compacte :

```text
Lundi                              [Ouvert ●]
09:00 → 13:00
14:00 → 18:00              [Pause déjeuner]
```

Jour fermé : une seule ligne `Dimanche — Fermé`, sans quatre champs horaires inutiles.

## Exceptions

Action `Ajouter une fermeture` → modale :
- date début * ;
- date fin * ;
- motif facultatif ;
- validation fin >= début ;
- mutation backend explicite ;
- la modale ne ferme qu'après succès.

Suppression d'une exception = confirmation simple puis DELETE existant ; ce n'est pas une suppression clinique, uniquement une règle de disponibilité future.

## Downstream Agenda

Avant toute modification visuelle de `AgendaStudio`, `DailyView` ou `WeeklyView`, produire une BEFORE dédiée sur les viewports concernés.

Puis :
- DailyView borne ses créneaux selon le jour sélectionné ;
- WeeklyView calcule une plage couvrant les jours ouverts de la semaine et matérialise les jours fermés ;
- les exceptions doivent être respectées pour l'affichage/disponibilité si le backend de rendez-vous le permet ; sinon afficher la fermeture sans prétendre bloquer côté backend avant preuve ;
- retirer le bouton mort `Nouveau Ticket` si aucune mécanique réelle n'est trouvée.

## Critères de succès

1. `Mode d'Agenda` absent de l'écran Settings.
2. `File d'attente (Tickets)` absente de l'écran Settings.
3. semaine 7 jours persistée réellement ; aucun état uniquement frontend.
4. fallback legacy préserve les anciens horaires.
5. fermeture/réouverture d'un jour sauvegardée.
6. horaires invalides bloqués avec message explicite.
7. exceptions/congés listés, ajoutables et retirables depuis Settings.
8. aucune suppression de colonne legacy dans R7.
9. Agenda downstream n'utilise plus une plage 08:00–19:00 codée en dur une fois le wiring réalisé.
10. BEFORE/AFTER mêmes viewports, aucun overflow, score visuel final.
11. tests backend + frontend + T2/CI proportionnés verts avant CLOSED.

## Hors scope

- moteur de réservation externe ;
- gestion multi-praticiens avec horaires individuels ;
- salle/fauteuil/ressource ;
- file d'attente Ticket complète ;
- suppression physique des champs legacy ;
- Vercel.
