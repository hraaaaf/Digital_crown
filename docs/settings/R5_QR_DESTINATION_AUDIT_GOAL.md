# R5 — QR documentaire : audit de destination

Date : 2026-08-19
Scope : Réglages → Design & Ambiance → QR documentaire + routes backend réellement encodées.

## Goal
Prouver pour chacun des 7 types de QR ce qui est réellement encodé et si la destination existe avant de modifier l'UI.

## Faits vérifiés

### UI
Les 7 types réellement exposés sont :
- `VCARD` — Contact ;
- `WEBSITE` — Site Web ;
- `INSTAGRAM` — Instagram ;
- `WHATSAPP` — WhatsApp ;
- `LOCATION` — Maps ;
- `VALIDATION` — Signature ;
- `PAYMENT` — Paiement.

Aucune action explicite `Tester / Scanner` n'est proposée dans l'UI actuelle.

### Payloads réellement encodés par `BaseTemplate._draw_qr_code`
- `VCARD` : utilise `qr_code_value` s'il est fourni ; sinon construit automatiquement une vCard depuis praticien/téléphone/email/adresse.
- `WEBSITE` : utilise `qr_code_value` et préfixe `https://` si nécessaire.
- `INSTAGRAM` : transforme `qr_code_value` en URL `https://instagram.com/...` si nécessaire.
- `WHATSAPP` : priorité à `qr_code_value`, sinon contact WhatsApp, sinon téléphone ; construit une URL `wa.me` avec message prérempli.
- `LOCATION` : construit une recherche Google Maps depuis l'adresse cabinet ; `qr_code_value` n'est pas utilisé par cette branche.
- `VALIDATION` : construit `${BACKEND_URL}/verify/<doc_id>`.
- `PAYMENT` : construit `${BACKEND_URL}/track/<doc_id>`.

### Routes backend réelles
`backend/routers/verification.py` déclare :
- `GET /verify/{public_id}/{document_type}` ;
- `GET /verify/{doc_id}` ;
- `GET /track/{doc_id}`.

Dans `backend/main.py`, ce router est monté avec le préfixe :
`/api/documents`.

Les destinations HTTP réelles sont donc :
- `/api/documents/verify/...` ;
- `/api/documents/track/...`.

### Défaut de câblage prouvé
Le générateur QR n'ajoute pas le préfixe `/api/documents` et le fallback `BACKEND_URL` vaut `http://localhost:8000`.

Avec ce contrat par défaut :
- `VALIDATION` encode `http://localhost:8000/verify/<doc_id>` alors que la route réelle est `http://localhost:8000/api/documents/verify/<doc_id>` ;
- `PAYMENT` encode `http://localhost:8000/track/<doc_id>` alors que la route réelle est `http://localhost:8000/api/documents/track/<doc_id>`.

Verdict : **les concepts Validation et Suivi de paiement sont utiles et les pages backend existent, mais leur destination QR est actuellement mal câblée**. Ne pas les supprimer ; corriger la construction d'URL et rendre la destination testable dans l'UI.

## Verdict par type

| Type | Verdict | Motif |
|---|---|---|
| VCARD | GARDER | payload autonome utile ; fallback profil réel |
| WEBSITE | GARDER / EXPLICITER | dépend entièrement de la valeur saisie |
| INSTAGRAM | GARDER / EXPLICITER | transformation URL simple et réelle |
| WHATSAPP | GARDER | fallback contacts/profil utile ; destination déterministe |
| LOCATION | GARDER / CLARIFIER | utilise l'adresse cabinet, pas le champ valeur générique |
| VALIDATION | CORRIGER | page de vérification réelle, URL générée sans `/api/documents` |
| PAYMENT | CORRIGER / RENOMMER | page de suivi réelle, URL générée sans `/api/documents` ; ce n'est pas un paiement en ligne |

## Recommandation R5 UI
1. remplacer le champ générique unique par une aide adaptée au type sélectionné ;
2. afficher la **destination exacte qui sera encodée** avant sauvegarde ;
3. ajouter une action `Tester la destination` pour les types URL ;
4. renommer `Signature` en **Vérification du document** : aucune signature électronique n'est effectuée ;
5. renommer `Paiement` en **Suivi du paiement** : la route affiche un état de paiement, elle n'encaisse rien ;
6. pour `Maps`, afficher clairement que la source est l'adresse du cabinet ;
7. corriger les URLs backend avant de présenter Validation/Suivi comme fonctionnels.

## Succès audit
1. inventaire exact des générateurs et payloads : **PROUVÉ** ;
2. routes `/verify` et `/track` : **PROUVÉES** ;
3. mismatch de préfixe : **PROUVÉ** ;
4. verdict par type : **ÉTABLI** ;
5. aucune modification produit effectuée dans cette phase d'audit.

Hors scope audit : refonte PDF, paiement en ligne, signature électronique, Vercel.