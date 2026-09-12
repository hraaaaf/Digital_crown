# P2 — Patient, actes et facturation multi-praticiens

## Goal

Ajouter un contexte praticien utile au dossier patient **sans déplacer ni réécrire les données locales existantes**, puis ventiler la production/les encaissements par praticien uniquement lorsque la donnée source le permet.

## Invariant local non négociable

- `patients` reste la liste canonique locale existante.
- `DocumentArchive` et les documents/fichiers locaux restent inchangés.
- Aucun backfill obligatoire des patients historiques.
- Aucune migration destructive de la table `patients`.
- Aucune dépendance cloud ajoutée.

Le référent patient est stocké dans une table additive `patient_practitioner_assignments` (0 ou 1 attribution par patient). La suppression de cette couche ne modifie pas le patient ni ses documents.

## Audit vérifié

- `Acte.praticien_id` existe déjà, est obligatoire et pointe vers `users.id`.
- `Payment.acte_id` est optionnel ; un paiement peut donc être réel sans être attribuable à un praticien.
- Un paiement d'échéance peut être attribué uniquement si son `InstallmentPlan` est lui-même lié à un acte.
- Le snapshot financier P6 agrège actuellement actes + paiements au niveau patient, sans ventilation par praticien.

## BEFORE UI

Baseline : commit `85cc4ca39df3d1064e1d82bb3a6a7048dc3e6d80`.

Run visuel : `34685062932` — success.

Matrice : Dossier / Finances / Modifier / Nouveau patient × 390x844 / 768x1024 / 1280x900 = 12 captures.

Mesures : 0 overflow horizontal et 0 pageerror sur les 12 captures.

Constats fonctionnels :

- Dossier : aucun référent clinique explicite.
- Finances : montants patient fiables mais aucun axe praticien visible.
- Modifier / Nouveau : formulaires locaux stables ; ils ne doivent pas être alourdis pour imposer une donnée référent non obligatoire.
- Documents : hors modification visuelle P2 ; le stockage local existant reste intact.

## Référence / mockup

Direction : **référent clinique compact + production praticien lisible**.

1. Dossier patient : carte compacte « Référent clinique » placée sous l'en-tête patient, avec praticien actuel, menu de changement et état « Non attribué » explicite.
2. Sélection : options issues d'un endpoint patient plan-independent, tenant-safe, limité aux praticiens assignables actifs/approuvés.
3. Finances : bloc « Production par praticien » au-dessus du détail des actes, avec Facturé / Encaissé lié / Reste lié par praticien.
4. Paiements non traçables vers un acte : bloc séparé « Encaissements non attribués », jamais répartis artificiellement.
5. Nouveau / Modifier : aucune obligation de choisir un référent ; les formulaires existants restent simples. L'attribution se fait depuis le dossier après création.

## Succès observable

- un patient historique sans attribution continue de s'ouvrir normalement ;
- attribuer/retirer un référent ne modifie aucune colonne de `patients` et aucun document ;
- un praticien d'un autre cabinet, inactif, pending ou secrétaire ne peut pas être référent ;
- la ventilation facturée provient de `Acte.praticien_id` ;
- l'encaissé par praticien ne compte que les paiements traçables vers ces actes ;
- le reliquat non attribuable reste visible séparément ;
- total facturé/encaissé/reste existants restent rétrocompatibles ;
- AFTER : mêmes 12 captures, 0 overflow, 0 runtime error.

## Hors périmètre P2

- modification/migration des documents locaux ;
- réattribution automatique des patients historiques ;
- partage arbitraire d'un paiement patient entre praticiens ;
- multi-site ;
- déploiement Vercel.
