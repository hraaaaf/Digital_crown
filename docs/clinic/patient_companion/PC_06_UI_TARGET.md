# PC-06 — Patient Finance — UI TARGET

Status: TARGET LOCKED BEFORE UI IMPLEMENTATION
Branch: feature/patient-companion-pc06-finance
Deployment: none

## Goal
Ajouter une surface mobile « Mes finances » qui montre uniquement la vérité financière fraîche du cabinet, sans créer d'état financier local faisant autorité.

## Target mobile
Viewports obligatoires : 360×800 et 390×844, Chromium + WebKit.

Ordre dans l'espace patient :
1. notifications/actions urgentes existantes ;
2. **Mes finances** ;
3. questionnaires / consentements / agenda existants selon l'ordre actuel.

## Surface « Mes finances »
- titre clair : « Mes finances » ;
- badge de vérité : « Données du cabinet » ;
- trois indicateurs lisibles : Facturé / Encaissé / Reste dû ;
- aucun bouton « payer » tant qu'aucun provider réel n'est certifié ;
- message explicite et neutre : « Paiement en ligne non activé par le cabinet » ;
- échéanciers existants : titre, montant total, échéances, date, statut ;
- historique des paiements : montant, date, moyen de paiement ;
- notes d'honoraires partagées : titre, date, montant, bouton « Télécharger » ;
- un téléchargement protégé doit réutiliser le Bearer Patient Companion, jamais une URL publique.

## États
- loading : skeleton/texte court, sans ancien montant ;
- erreur réseau : ne pas afficher de valeur financière stale comme vérité ; proposer « Réessayer » ;
- hors ligne/non synchronisé : « Reconnexion au cabinet requise pour actualiser les données financières » ;
- vide : 0 MAD + listes vides, sans dramatisation ;
- session révoquée/expirée : surface non chargée.

## Contraintes UX
- aucune donnée financière persistée dans le coffre local PC-06 V1 ;
- aucune valeur financière dans notification OS ;
- touch targets >= 44 px ;
- pas de scroll horizontal ;
- valeurs alignées et lisibles à 360 px ;
- contraste et focus clavier visibles ;
- aria-live pour état de chargement/erreur ;
- format MAD et dates locale fr-FR.

## Success visuel
- hiérarchie immédiate : reste dû visible sans dominer agressivement ;
- aucun faux CTA de paiement ;
- factures téléchargeables seulement si partagées ;
- échéanciers/paiements compacts, pas de tableau desktop ;
- cohérent avec cartes arrondies Patient Companion existantes.

## Proof
- BEFORE : écran Patient Companion sans surface finance, mêmes viewports ;
- AFTER : surface finance avec fixture déterministe ;
- Chromium + WebKit, 360×800 / 390×844 ;
- frontend truth-boundary tests ;
- score visuel conservateur + revue humaine avant closeout.
