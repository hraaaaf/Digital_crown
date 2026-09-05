# Digital Crown — MOB-5B Frontdesk Mobile — Implementation state

Status: IMPLEMENTED / VALIDATION PENDING
Date: 2026-09-05
Branch: `ux/mobile-frontdesk-mob5b`
Baseline: `89098066ef0c943c0e084af4b9cd388d3ab0aa5b`

## Implémenté
- nouveau tab `frontdesk` dans le dashboard mobile ;
- `Plus → Frontdesk` pour DENTISTE / ADMIN / SECRETAIRE ;
- deep link canonique `/mobile/dashboard?tab=frontdesk` ;
- vue mobile dédiée consommant `GET /appointments/pending` ;
- confirmer / refuser / demander confirmation via endpoints existants ;
- appel direct et WhatsApp conditionnels au téléphone ;
- aucun faux statut d'envoi WhatsApp ;
- erreurs inline ;
- confirmation de refus via dialog mobile ;
- état vide dédié ;
- tests ciblés navigation/routage/vue ajoutés.

## Validation encore requise
- CI frontend/backend ;
- build production ;
- runtime ;
- AFTER 390×844 / 430×932 / 768×1024 ;
- comparaison visuelle + score ;
- proof canonical ;
- PR ready puis merge.

Deployment: none. No Vercel deployment authorized.
