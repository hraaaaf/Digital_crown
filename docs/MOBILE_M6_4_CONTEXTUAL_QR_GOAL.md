# Mobile M6.4 — Contextual QR Bridge — Goal visuel

## Goal

Faire comprendre avant scan **qui** sera appairé et **où** le téléphone arrivera, puis conserver cette destination sur le mobile après l'appairage.

## BEFORE à mesurer

- Bridge desktop `MobileSecurity` : 768×1024 et 1280×900, QR masqué + QR révélé.
- Onboarding mobile : 390×844, 430×932 et 768×1024.
- Mesures : overflow, erreurs console/page, hauteur des contrôles, hiérarchie et libellés.

## Cible visuelle

### Desktop

Carte `Compagnon Mobile` :

1. **Utilisateur** — select explicite du membre actif du cabinet.
2. **Ouvrir sur** — destination mobile explicite (Agenda, Finance, Labo, Assistant, Sécurité, Équipe, SuperAdmin selon droits).
3. **Générer le pont mobile** — CTA principal >=48 px.
4. QR + code manuel affichés seulement après génération.
5. Résumé visible : `Dr … → Agenda`, durée de validité, mention « aucune donnée patient dans le QR ».
6. Révocation reste séparée et visuellement dangereuse.

### Mobile

Après échange sécurisé :

- succès explicite ;
- libellé de destination visible (`Ouverture : Agenda`, etc.) ;
- redirection réelle vers la surface demandée ;
- si destination invalide/non permise : retour sûr vers Agenda avec message non ambigu.

## Critères

- cibles tactiles >=44 px ;
- pas d'identifiant patient/PHI dans l'URL QR ;
- pas de destination arbitraire ; allowlist uniquement ;
- aucune route desktop injectée telle quelle dans le mobile ;
- cohérence avec le style existant Digital Crown ; pas de redesign gratuit.

Référence wireframe : `.audit/mobile-m64-contextual-qr-mockup.svg`.
