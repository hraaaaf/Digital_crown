# START PROMPT — Digital Crown / Agenda clinique — LOT A3

HANDOVER — DIGITAL CROWN / AGENDA CLINIQUE — A3

Repo:
`hraaaaf/Digital_crown`

Fichier canonique:
`docs/audits/AGENDA_CLINIC_CANONICAL.md`

Handover précédent:
`docs/audits/AGENDA_CLINIC_A2_HANDOVER.md`

## Première action obligatoire

Avant toute modification:

1. Lire intégralement `docs/audits/AGENDA_CLINIC_CANONICAL.md`.
2. Lire intégralement `docs/audits/AGENDA_CLINIC_A2_HANDOVER.md`.
3. Vérifier GitHub live:
   - SHA actuel de `master`;
   - présence réelle du merge A2 dans son historique;
   - état éventuel de la PR #533;
   - CI/certifications post-merge pertinentes;
   - PR ouvertes pertinentes;
   - reviews/threads;
   - divergence réelle.
4. Ne jamais supposer qu'un SHA ou un statut CI du handover est encore actuel.
5. Si A2 n'est pas mergé ou si son post-merge est bloquant, terminer A2 avant de démarrer A3.
6. Si A2 est proprement mergé, travailler uniquement sur A3.

## Goal global du chantier

Faire évoluer l'agenda vers un agenda clinique multi-dentistes complet sans casser:

`Appointment + employer_id + praticien_id + logique de conflits existante`.

## A3 — Goal exact

Ajouter les disponibilités individuelles de chaque praticien:
- horaires de travail;
- jours travaillés;
- pauses;
- congés;
- absences/exceptions individuelles;

en les superposant aux horaires et fermetures globaux du cabinet.

Principe canonique:

`disponibilité effective = disponibilité cabinet ∩ disponibilité praticien`.

## Baseline technique à revalider

État vérifié avant A3:
- `cabinet_settings.weekly_schedule_json` contient les horaires globaux du cabinet, tenant-scoped par `employer_id`;
- `agenda_exceptions` contient les fermetures globales, tenant-scoped par `employer_id`;
- `backend/services/agenda_availability.py::validate_appointment_availability(...)` applique ces règles globales;
- A2 réutilise ces règles cabinet-wide et n'introduit aucune disponibilité individuelle;
- le moteur de conflits accepte `praticien_id` et traite `praticien_id = NULL` comme bloqueur global.

Ne choisis aucun schéma A3 avant d'avoir réinspecté les modèles, migrations, contraintes, chemins d'upgrade et contrats API actuels.

## Succès observable attendu

A3 est réussi seulement si:
- chaque praticien peut avoir un planning hebdomadaire propre;
- chaque praticien peut avoir des pauses propres;
- chaque praticien peut avoir des congés/absences/exceptions propres;
- une fermeture globale cabinet bloque tous les praticiens;
- une indisponibilité individuelle bloque uniquement le praticien concerné;
- un autre praticien peut rester disponible au même créneau;
- la grille A2 rend visuellement ces indisponibilités sans perdre l'axe synchronisé;
- la création depuis une lane refuse côté serveur un praticien indisponible;
- l'édition/réaffectation revalide également la disponibilité individuelle côté serveur;
- les vues Jour/Semaine/Mois filtrées A1 restent cohérentes;
- les rendez-vous historiques `praticien_id = NULL` restent des bloqueurs globaux;
- les cabinets/praticiens existants gardent un comportement compatible par défaut;
- aucune donnée existante n'est détruite;
- toute migration nécessaire est additive et upgrade-safe;
- tests backend + frontend + navigateur/non-régression proportionnels au risque sont verts;
- toute évolution visuelle est certifiée BEFORE/AFTER aux mêmes viewports.

## Process UI/UX obligatoire

Avant toute modification visuelle A3:

1. capturer un BEFORE réel de la grille A2 sur les viewports cibles;
2. écrire le Goal observable A3;
3. produire/figer une référence ou mockup des états:
   - praticien disponible;
   - hors horaires individuels;
   - pause individuelle;
   - congé/absence;
   - fermeture globale cabinet;
4. implémenter seulement après référence figée;
5. capturer l'AFTER aux mêmes viewports;
6. comparer BEFORE/AFTER;
7. tester les règles backend et les flux création/édition;
8. attribuer un score visuel uniquement sur preuve observable.

## Architecture / sécurité

Toujours préserver:
- isolation `employer_id`;
- attribution `praticien_id`;
- DB, patients, documents et rendez-vous existants;
- comportement A1 Jour/Semaine/Mois;
- grille synchronisée A2;
- legacy non assigné comme bloqueur global;
- absence de réaffectation silencieuse.

Recommandation d'architecture à vérifier avant implémentation:
- couche individuelle additive distincte des réglages globaux cabinet;
- fermeture globale toujours prioritaire;
- disponibilité individuelle évaluée après la disponibilité globale;
- validation serveur autoritaire; le frontend ne doit jamais être la seule barrière.

## Hors scope A3

- A4: fauteuils, salles, ressources physiques et collisions de ressources;
- A5: timezone cabinet explicite, soft-delete/historique, stratégie/migration legacy;
- refonte générale du moteur de collision;
- déploiement Vercel.

## Non-régression obligatoire

Toute modification significative doit prouver:
- aucune régression DB/upgrade;
- aucune perte de données patients/documents/rendez-vous;
- création et édition existantes toujours compatibles;
- collisions praticien préservées;
- fermetures globales préservées;
- A1 et A2 préservés.

## Gates humains

- aucun merge sans accord utilisateur explicite sur le HEAD exact;
- aucun déploiement Vercel sans autorisation explicite.

## Next exact

Après la vérification GitHub initiale et uniquement si A2 est réellement mergé/post-merge propre:

1. auditer les modèles, migrations et services de disponibilité actuels;
2. capturer le BEFORE A3;
3. écrire Goal / Success / Proof A3;
4. figer la référence UX et le contrat de persistance avant toute modification de schéma ou UI.
