# START PROMPT — Digital Crown / Agenda clinique — LOT A2

HANDOVER — DIGITAL CROWN / AGENDA CLINIQUE — A2

Repo:
`hraaaaf/Digital_crown`

Fichier canonique:
`docs/audits/AGENDA_CLINIC_CANONICAL.md`

Handover précédent:
`docs/audits/AGENDA_CLINIC_A1_HANDOVER.md`

Première action obligatoire:

1. Lire intégralement `docs/audits/AGENDA_CLINIC_CANONICAL.md`.
2. Lire intégralement `docs/audits/AGENDA_CLINIC_A1_HANDOVER.md`.
3. Vérifier sur GitHub le master ACTUEL, la présence du merge A1 dans son historique, les PR ouvertes pertinentes, les CI et la divergence réelle.
4. Ne supposer aucun SHA ou statut CI ci-dessous encore actuel.
5. Si un gate post-merge A1 pertinent est rouge, diagnostiquer/corriger avant A2.
6. Si les gates sont verts, travailler uniquement sur A2.

État A1 vérifié au handover:
- PR #528 mergée;
- branche A1: `feat/agenda-clinic-a1-practitioner-filter-20260916`;
- HEAD exact pré-merge: `9e3d9e8de8362b8bb4d69e908e1c68b971d43f51`;
- merge commit A1: `86958c913e5c2872504505eb3af0485b22e66c05`;
- CI pré-merge #4520: SUCCESS;
- T2 Runtime Browser #3392: SUCCESS;
- PostgreSQL #907: SUCCESS;
- Visual P1 #109: SUCCESS;
- M6-I #2192: SKIPPED attendu;
- aucun commentaire/review/thread au dernier contrôle avant merge.

Post-merge observé:
- CI push #4527 sur `86958c9...`: CANCELLED parce que master a avancé immédiatement après;
- master observé ensuite: `8a37913c23f182a8de4e0f1dd0e2049e48b7267f`;
- ce master contenait `86958c913e5c2872504505eb3af0485b22e66c05` comme parent;
- CI #4528 et PostgreSQL #912 étaient QUEUED au dernier contrôle.

Ne jamais transformer ces deux derniers états en SUCCESS sans vérification GitHub fraîche.

LOT A2 — Vue clinique multi-praticiens

Goal exact:
remplacer la lecture multi-praticiens actuelle en listes verticales par une vraie grille horaire synchronisée par praticien, sans modifier encore les disponibilités individuelles A3.

Cible UX:
`Heure | Dr A | Dr B | Dr C ...`

Succès observable attendu:
- axe horaire commun synchronisé;
- une colonne par praticien actif/assignable;
- rendez-vous rendus dans la bonne colonne et au bon créneau;
- création depuis une colonne attribue explicitement le praticien correspondant;
- édition ne réaffecte jamais silencieusement;
- comportement legacy non assigné visible/explicite sans masquer les bloqueurs globaux;
- responsive utilisable sur les viewports cibles;
- comportement existant Jour/Semaine/Mois A1 préservé;
- aucun changement DB inutile;
- tests frontend/backend/non-régression proportionnels au risque;
- certification visuelle avec preuves BEFORE/AFTER.

Hors scope A2:
- horaires individuels, jours travaillés, pauses, congés, absences — A3;
- fauteuils/salles/ressources — A4;
- timezone cabinet explicite, soft-delete/historique, migration legacy — A5;
- réécriture de la logique de collision déjà validée.

Process UI/UX obligatoire avant implémentation:
BEFORE → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel.

N'implémente rien avant d'avoir figé le BEFORE et la référence de grille.

Sécurité:
- préserver DB, patients, documents et fonctionnalités validées;
- aucune migration destructive;
- aucune réaffectation silencieuse;
- préserver isolation `employer_id`;
- préserver collisions par praticien;
- aucun merge sans accord utilisateur explicite sur le HEAD exact;
- aucun déploiement Vercel sans autorisation explicite.

Next exact:
faire la vérification GitHub fraîche, puis si les gates A1 sont verts, capturer le BEFORE A2 et proposer la référence/mockup de grille multi-praticiens avant tout code.
