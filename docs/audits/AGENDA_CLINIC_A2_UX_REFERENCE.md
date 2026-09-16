# Agenda clinique — A2 UX reference

Date : 2026-09-16  
Lot : A2 — Vue clinique multi-praticiens  
PR : #533  
Base produit BEFORE : `bc3d8d145670dc70dc6c6842e772e56d1d89aa99`

## BEFORE — preuve figée avant implémentation

Workflow : `Agenda A2 BEFORE Visual Certification`  
Run : `#1` / `35084989399` — SUCCESS  
HEAD de capture : `2911da0f4e8bd4766b725089924e5ba5a616eaff`  
Artifact : `agenda-a2-before-visual-evidence`  
Digest : `sha256:c4fc22b6a489170e06b5a7f6ff09f76cdaa2e68ac40cec82c5bdd55abc7a3755`

Viewports immuables pour la comparaison A2 :

- 390 × 844
- 768 × 1024
- 1280 × 900

Constats observables du BEFORE :

1. La vue Multi affiche une colonne par praticien mais les rendez-vous sont des cartes empilées verticalement ; aucun axe horaire partagé ne permet de comparer les disponibilités.
2. Les cartes contiennent des rendez-vous de plusieurs jours alors que l'en-tête affiche une date unique.
3. `legacy_unassigned` est bien présent dans le contrat backend mais n'est pas rendu dans la vue Multi ; le harness confirme `multiText=false` aux trois viewports.
4. À 390 px, la troisième colonne devient visuellement tronquée : la page ne déborde pas globalement mais la lecture multi-praticiens n'est pas exploitable.
5. Les flèches précédent/suivant ne modifient pas la date lorsque `viewMode === 'multi'` dans l'implémentation BEFORE.

Aucun fichier produit n'a été modifié pour obtenir ces captures.

## GOAL A2 — résultat exact

Remplacer la lecture Multi actuelle par une grille journalière synchronisée :

`Heure | Dr A | Dr B | Dr C | ...`

Le même axe temporel doit permettre de voir immédiatement les créneaux libres et occupés de tous les praticiens actifs/assignables, tout en conservant les règles existantes d'attribution, de collision et d'isolation cabinet.

## Succès observable

- axe horaire commun ;
- une lane par praticien actif/assignable renvoyé par l'API existante ;
- rendez-vous exact positionné dans la bonne lane et à sa vraie heure/durée ;
- clic sur un créneau libre ouvre la création avec `praticien_id` explicitement fixé à la lane ;
- le contrôle de conflit de cette création utilise le même `praticien_id` ;
- édition d'un rendez-vous existant sans réaffectation silencieuse ;
- rendez-vous legacy `praticien_id = NULL` affiché comme bloqueur transversal explicite, jamais attribué artificiellement ;
- rendez-vous flexibles conservés dans une zone dédiée sans leur inventer une heure ;
- horaires globaux du cabinet réutilisés ; aucune disponibilité individuelle A3 ;
- Jour / Semaine / Mois A1 inchangés ;
- aucune migration DB ;
- aucune modification du moteur backend de collision si le contrat actuel suffit.

## Référence UX figée avant implémentation

Référence visuelle : `docs/audits/AGENDA_CLINIC_A2_REFERENCE.svg`.

Décisions :

- Multi devient une vue **journalière**. Les flèches de navigation font J-1 / J+1 et `Aujourd'hui` conserve son comportement existant.
- Résolution visuelle : slots de 15 min, 80 px par heure, même convention que la vue Semaine existante.
- L'axe horaire reste fixe à gauche.
- Chaque lane praticien a une largeur minimale de 220 px.
- Desktop : les lanes utilisent toute la largeur disponible.
- Tablette/mobile : la grille garde sa structure temporelle et devient horizontalement scrollable ; elle ne retombe jamais en listes verticales.
- Les en-têtes praticiens restent associés aux lanes pendant le défilement.
- Les intervalles fermés selon les horaires globaux existants sont grisés et non créables.
- Les rendez-vous existants hors horaires ne doivent pas disparaître : la plage visible s'étend si nécessaire pour les contenir.
- Un legacy exact-time est une bande transversale à l'heure réelle avec libellé `Non assigné — bloque tous les praticiens`.
- Les rendez-vous flexibles (`MORNING`, `AFTERNOON`, `FULL_DAY`) restent visibles dans une bande dédiée au-dessus de la timeline ; A2 ne leur invente pas de placement horaire.
- Le modal indique le praticien choisi lors d'une création depuis une lane.

## Contrat de sécurité

Création depuis une lane :

- `AgendaModal` reçoit le praticien de lane ;
- le GET `/appointments/check-conflicts` reçoit explicitement ce praticien ;
- le POST `/appointments/` reçoit explicitement ce praticien ;
- l'intercepteur A1 conserve cet identifiant car il n'écrase jamais une valeur explicite.

Édition :

- aucun `praticien_id` ajouté automatiquement au PUT ;
- le praticien historique reste autoritaire ;
- un legacy édité reste legacy tant qu'aucune action explicite de migration/réaffectation n'existe — hors scope A2.

## Hors scope maintenu

A3 : horaires individuels, jours travaillés, pauses, congés, absences.  
A4 : fauteuils, salles, ressources physiques.  
A5 : timezone cabinet explicite, soft-delete/historique, migration legacy.

## AFTER obligatoire

L'AFTER doit être recapturé exactement en 390×844, 768×1024 et 1280×900 avec les mêmes fixtures fonctionnelles, puis comparé au BEFORE sur : lisibilité temporelle, lane correcte, legacy visible, responsive, absence d'overflow de page, absence d'erreur runtime et création explicite par lane.
