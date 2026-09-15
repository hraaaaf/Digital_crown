# Prescription Medication Catalog — AMMPS 2026 supplement

Status: VALIDATED — PRE-MERGE

## Goal

Après saisie exacte `ACIG` dans l’Ordonnance, afficher une présentation documentaire vérifiée d’ACIGAM sans sélectionner automatiquement de médicament, sans ajouter de règle clinique et sans falsifier le snapshot CNOPS 2021.

## Success

- `GET /api/medications/search?q=ACIG` retourne au moins une présentation ACIGAM documentée ;
- ACIGAM porte une provenance AMMPS explicite ;
- la source CNOPS historique reste inchangée et ses identifiants restent stables ;
- l’UI n’affiche plus un bandeau CNOPS 2021 pour une présentation provenant de l’AMMPS ;
- aucune présentation n’est sélectionnée automatiquement ;
- tests ciblés + régression générale applicables verts ;
- AFTER 1280x900 sur le même scénario que la baseline BEFORE.

## Sources vérifiées

Source primaire actuelle : AMMPS, `Répertoire Marocain des Médicaments Génériques`, édition projet janvier 2026.

Entrée intégrée :
- ACIGAM 200 MG COMPRIME SECABLE BOITE DE 20
- DCI : ACIDE TIAPROFENIQUE
- EPI : BOTTU
- EAN13 : 6118000041986
- voie : ORALE

Cross-check réglementaire : Bulletin Officiel marocain n°7262 du 4 janvier 2024, qui liste ACIGAM 100 mg et 200 mg dans l’annexe de révision des prix.

Aucune disponibilité instantanée en pharmacie n’est déduite de ces sources.

## BEFORE

Baseline dédiée : PR #506, master de départ `647f682ea71e026e7e9604fc0ca419e2ae6f7a44`.

Scénario : ouvrir Ordonnance, saisir exactement `ACIG`, ne rien sélectionner, capturer 1280x900.

Preuve BEFORE : Fidelity #141, artifact `10388957731`, `suggestionCount: 0`.

## Mockup / référence cible

```text
MÉDICAMENT 01
[ 🔍 ACIG                                      ]
┌──────────────────────────────────────────────┐
│ Référentiels documentaires marocains         │
│ provenance indiquée par présentation         │
├──────────────────────────────────────────────┤
│ ACIGAM 200 MG COMPRIME SECABLE BOITE DE 20  │  200 MG
│ ACIDE TIAPROFENIQUE                          │  COMPRIME SECABLE
│ AMMPS · 2026-01 · statut actuel non certifié │
└──────────────────────────────────────────────┘
```

Aucun bouton d’application automatique, aucune posologie, aucune recommandation thérapeutique.

## Implementation contract

- conserver `medications_ma.json` comme snapshot CNOPS 2021 inchangé ;
- ajouter un supplément AMMPS séparé ;
- provenance par enregistrement ;
- priorité à la source AMMPS lorsqu’une présentation documentaire identique existe dans plusieurs sources ;
- identifiants CNOPS existants inchangés ;
- identifiants AMMPS avec préfixe distinct ;
- fail closed si source ou donnée absente.

## Closeout evidence

Validation visuelle propriétaire : ACCEPTÉE le 2026-09-15 sur la capture AFTER 1280x900.

Dernier HEAD fonctionnel certifié avant ce closeout documentaire : `2004504774887b2a020e16d86d3c02868380d024`.

Preuves exact-head :
- Ordonnance Fidelity V3 Visual Certification #173 : SUCCESS ;
- artifact `ordonnance-fidelity-v3-evidence` id `10391109630`, head SHA `2004504774887b2a020e16d86d3c02868380d024`, digest `sha256:b4e876770d0347cad59c8957e41bf3e5cf432f926a4327318d639ea6fce31fda` ;
- CI #4311 : SUCCESS ;
- Catalog Connected Truth Certification #1254 : SUCCESS ;
- Cabinet Upgrade PostgreSQL Certification #717 : SUCCESS ;
- Settings R11 TemplateBuilder Dependency Audit #742 : SUCCESS ;
- T2 Runtime Browser Certification #3202 : SUCCESS ;
- Patient P7 Final Certification #1643 : SUCCESS.

AFTER mesuré sur le HEAD fonctionnel certifié : saisie `ACIG`, une suggestion ACIGAM visible, source `ammps-rmmg-2026-01`, aucune sélection automatique, champ conservé à `ACIG`, aucune erreur page.

Comparaison BEFORE → AFTER : `0 suggestion` → `ACIGAM` documenté et sourcé AMMPS, sans autofill clinique. La modification du test frontend obsolète a ensuite été certifiée par CI #4311 sans modification de logique produit.

Score visuel de conformité au mockup : 10/10 sur les critères contractuels observables (suggestion, identité, DCI, provenance, absence de sélection automatique). Ce score mesure la conformité au mockup, pas une appréciation esthétique générale.

Merge autorisable uniquement après certification du commit documentaire de closeout et vérification finale de la PR. Aucun déploiement Vercel.
