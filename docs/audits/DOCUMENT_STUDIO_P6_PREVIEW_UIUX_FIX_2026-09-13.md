# Document Studio — P6 Live Preview UI/UX fix

Date : 2026-09-13
Baseline : `5b12727644aeb115be29ff5da2435a8670eb18d1`

## BEFORE — défaut observé

Le Live Preview non-inline utilisait un drawer droit dès le breakpoint `sm` (>= 640 px) : `sm:left-auto sm:right-4 sm:w-[min(600px,calc(100vw-2rem))]`.

Conséquences vérifiées par source et par capture fournie pendant la revue :

- à 768 px, le drawer de presque 600 px laisse une bande du Studio derrière et crée une hiérarchie visuelle ambiguë ;
- à 1280 px, le panneau recouvre une part importante du dossier patient/Studio sans vraie logique de split-view ;
- `DocumentHubPreview` ajoutait en plus un conteneur `fixed` alors que `LivePreview` se portale déjà dans `document.body`, créant une couche fixe redondante ;
- la certification P6 existante vérifiait l’éditeur sans ouvrir ni mesurer la géométrie du preview.

## Goal

1. 390 et 768 px : le preview vient **au-dessus** du Studio et occupe l’espace utile, sans colonne latérale concurrente.
2. 1280 px : le preview est une vraie surface modale centrée et plafonnée, avec backdrop ; aucun ancrage à droite ne doit étouffer le Studio.
3. Le fond est bloqué aux interactions pointeur et le scroll document est verrouillé pendant l’ouverture.
4. `Fermer`, `Escape`, `Actualiser`, téléchargement, plein écran et rendu PDF restent fonctionnels.
5. Aucune modification de logique documentaire, clinique ou PDF.

## Référence / mockup fonctionnel

Références internes :

- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionGuideModal.tsx` : `fixed inset-0` + backdrop + surface modale centrée ;
- warning impression de `StudioFooter.tsx` : overlay explicite au-dessus du Studio.

### Mobile / tablette

```text
┌────────────────────────────────────┐
│ Aperçu document     Actualiser  X  │
├────────────────────────────────────┤
│                                    │
│            PDF / état vide         │
│                                    │
├────────────────────────────────────┤
│      Télécharger / Plein écran     │
└────────────────────────────────────┘
```

Le Studio n’est pas utilisé comme deuxième colonne derrière le preview.

### Desktop

```text
████████████ backdrop ████████████████
██      ┌──────────────────────┐     ██
██      │      Live Preview    │     ██
██      │   centré / max 5xl   │     ██
██      └──────────────────────┘     ██
██████████████████████████████████████
```

## Contrat AFTER

Le probe navigateur P6 doit désormais, aux viewports 390x844, 768x1024 et 1280x900 :

- ouvrir le preview ;
- capturer `p6-<viewport>-preview.png` ;
- prouver que l’overlay couvre le viewport ;
- prouver que le dialogue reste entièrement dans le viewport ;
- pour `<1024`, prouver que sa largeur est >= 90 % du viewport ;
- pour `>=1024`, prouver qu’il est centré et <= 1024 px environ ;
- fermer via Escape et vérifier sa disparition ;
- conserver les contrôles éditeur sans clipping et sans page error.

Aucun PASS visuel final n’est revendiqué avant l’exécution de ce probe sur le HEAD de correction.
