# M4 — Matrice finale ressources — Closeout

Date : 2026-08-25
État : CLOSED

## Goal

Fermer le Mobile Bridge contextuel sur ses états de sûreté et de reprise : expiration, usage unique, non-pairé, permission révoquée, ressource supprimée, backend local inaccessible et retour mobile, sans fuite technique ni affaiblissement du protocole.

## Produit final

- PR : #247
- HEAD produit certifié : `03d1150a8071088890bdfd431e845d55e7930f98`
- merge master : `d8561c441987047db4cf67ddb6b764c33a9d72f3`
- 1 commit / 1 fichier / 0 behind avant merge
- seul changement produit : les erreurs de transport navigateur `fetch` sont remplacées par un message utilisateur explicite
- les détails métier renvoyés par le backend restent inchangés
- aucun changement pairing / permission / context key / device binding / ressource

Message réseau canonique :

> Serveur du cabinet inaccessible. Vérifiez que le poste cabinet est démarré et accessible sur ce réseau, puis réessayez.

## BEFORE

Run `32844773286` — SUCCESS comme banc de preuve.

- non-pairé : explicite
- permission `agenda` révoquée : explicite
- ressource supprimée : explicite
- retour exact : `/mobile/dashboard?tab=agenda`
- token expiré : refusé sans consommation
- token : usage unique
- 0 overflow horizontal
- contrôles visibles >= 44 px
- régressions Patient / Panoramique / Document / Rendez-vous : PASS
- défaut confirmé : backend inaccessible affichait le message navigateur brut `Failed to fetch`

## Goal visuel / mockup

Référence verrouillée avant correctif : `.audit/mobile-m4-final-mockup.svg` sur la branche d'audit `audit/mobile-m4-final-matrix-20260825`.

Le contrat imposait de conserver le composant, sa hiérarchie et ses CTA et de remplacer uniquement le détail technique par le message métier.

## AFTER exact-head

Run `32846387701` — SUCCESS.

Artifact `9562601793`
Digest `sha256:ef564a2c604589103335e35e4e8018bb60dce1e5d0ef3ab2bc0be4910b90cf99`

Produit exact : `03d1150a8071088890bdfd431e845d55e7930f98`

- 6/6 états capturés
- non-pairé / révoqué / supprimé : explicites
- backend inaccessible : message métier exact sur 390 × 844 et 768 × 1024
- aucune chaîne réseau technique brute visible
- retour Agenda exact
- 0 overflow horizontal
- 0 contrôle visible < 44 px
- frontend build : PASS
- expiration terminale + non-consommation : PASS
- usage unique : PASS
- régressions M4-A/B/C/D : PASS
- les états non-pairé / révoqué / supprimé / ready sont pixel-identiques BEFORE ↔ AFTER ; seuls les écrans réseau changent

Score visuel final : **9,7/10**.

## CI exact-head

- CI globale #1841 / run `32846419447` : SUCCESS
- T2 Runtime Browser Certification #999 : SUCCESS
- Catalog Connected Truth Certification #272 : SUCCESS
- Patient P7 Final Certification #298 : SUCCESS

## Conclusion M4

Le lot M4 Mobile Bridge contextuel est CLOSED :

- Patient : CLOSED
- Panoramique : CLOSED
- Document : CLOSED
- Rendez-vous : CLOSED
- matrice finale erreurs / retour / expiration : CLOSED

Le prochain lot canonique est **M6 — Mobile-first réel**.

Aucun Vercel.
