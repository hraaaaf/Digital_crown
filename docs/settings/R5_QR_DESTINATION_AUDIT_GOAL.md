# R5 — QR documentaire : audit de destination

Date : 2026-08-19
Scope : Réglages → Design & Ambiance → QR documentaire + routes backend réellement encodées.

## Goal
Prouver pour chacun des 7 types de QR ce qui est réellement encodé et si la destination existe avant de modifier l'UI.

## Faits déjà vérifiés
- UI : `VCARD`, `LINK`, `INSTAGRAM`, `WHATSAPP`, `LOCATION`, `VALIDATION`, `PAYMENT`.
- `BaseTemplate` construit automatiquement VCARD et LOCATION.
- LINK/Instagram/WhatsApp utilisent `qr_code_value`.
- VALIDATION construit `${BACKEND_URL}/verify/<doc_id>`.
- PAYMENT construit `${BACKEND_URL}/track/<doc_id>`.
- aucune action explicite `Tester / Scanner` dans l'UI actuelle.

## Succès
1. grep backend complet des routes/endpoints contenant `/verify` et `/track` ;
2. inventaire exact des générateurs QR et payloads ;
3. verdict par type : FONCTIONNEL / À CORRIGER / À RETIRER ;
4. aucune modification produit avant preuve.

Hors scope : refonte PDF, paiement en ligne, signature électronique, Vercel.
