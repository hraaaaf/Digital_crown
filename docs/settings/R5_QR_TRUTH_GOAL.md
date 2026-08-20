# R5 — QR documentaire : vérité de destination + UX explicite

Date : 2026-08-20
Base : master `209e20f3dd38b11de387887dcb55d5aee76690f6`
Scope : Réglages → Design & Ambiance → Code QR + construction des URLs VALIDATION/PAYMENT.

## Goal
Conserver les 7 types QR utiles, corriger les destinations documentaires réellement cassées et rendre l’UI fidèle à ce qui sera encodé, sans inventer de signature électronique ni de paiement en ligne.

## Faits revalidés
- UI : `VCARD`, `WEBSITE`, `INSTAGRAM`, `WHATSAPP`, `LOCATION`, `VALIDATION`, `PAYMENT`.
- libellés actuels trompeurs : `Signature` et `Paiement`.
- `VALIDATION` encode actuellement `${BACKEND_URL}/verify/<doc_id>`.
- `PAYMENT` encode actuellement `${BACKEND_URL}/track/<doc_id>`.
- router réel monté sous `/api/documents` : `/api/documents/verify/...` et `/api/documents/track/...`.
- le champ générique `Lien / Numéro / Identifiant` n’est affiché que pour Website / WhatsApp / Instagram.

## Verdict produit
- VCARD : garder.
- WEBSITE : garder, expliciter URL.
- INSTAGRAM : garder, expliciter identifiant/URL.
- WHATSAPP : garder, expliciter numéro/URL.
- LOCATION : garder, préciser “adresse du cabinet”.
- VALIDATION : garder + corriger URL + renommer `Vérification du document`.
- PAYMENT : garder + corriger URL + renommer `Suivi du paiement`.

## Goal visuel
Le bloc QR doit expliquer la source/destination sans ajouter de jargon ni faire croire à une capacité inexistante.

### Wireframe cible
```text
Code QR                                      [ON]

[ Contact ] [ Site Web ]
[ Instagram ] [ WhatsApp ]
[ Maps ] [ Vérification du document ]
[ Suivi du paiement ]

Vérification du document
Le QR ouvre la page de vérification du document généré.
Destination : /api/documents/verify/<document>

ou, pour Suivi du paiement :
Le QR ouvre l’état de paiement du document. Aucun paiement n’est encaissé ici.
Destination : /api/documents/track/<document>
```

Pour Website / Instagram / WhatsApp : conserver un champ éditable mais avec label et placeholder adaptés au type.
Pour Maps : afficher que la source est l’adresse du cabinet, sans champ factice.

## Succès
1. BEFORE réel sur 1440 / 1024 / 768 / 430 / 390 avant modification produit.
2. Aucun overflow horizontal et aucune erreur runtime sur les 5 viewports AFTER.
3. `Signature` absent ; `Vérification du document` visible.
4. `Paiement` remplacé par `Suivi du paiement` avec avertissement explicite qu’il n’y a aucun encaissement.
5. VALIDATION encode `/api/documents/verify/<doc_id>`.
6. PAYMENT encode `/api/documents/track/<doc_id>`.
7. WEBSITE / INSTAGRAM / WHATSAPP ont une aide adaptée ; LOCATION indique sa source réelle.
8. VCARD et tous les autres payloads existants restent inchangés hors correction ciblée.
9. Build frontend + tests ciblés QR + T2/CI pertinents verts ou équivalence strictement documentée.

## Hors scope
- paiement en ligne ;
- signature électronique ;
- refonte générale des documents ;
- migration DB ;
- Vercel.
