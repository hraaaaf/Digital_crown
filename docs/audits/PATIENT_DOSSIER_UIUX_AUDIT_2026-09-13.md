# Audit UI/UX — Dossier patient Digital Crown

Date : 2026-09-13

## État vérifié

T1 Document Studio est fermé : PR #465 squash-mergée, master post-merge `b9fc9ca6f0e978d51fa2180c30143b2c2c047200` vérifié.

UX1-A/B est fermé : PR #467 squash-mergée sur master `0ca44f224f03d31f8d322498484fe2bfcd5d66e9`.

UX1-C est porté par la PR #468, branche `ux/patient-dossier-overlays`.

La preuve produit/visuelle de référence UX1-C est le HEAD `b73f2c7173637c8a867e6d97cb3aa197b475728a`. Le présent closeout documentaire crée un nouveau HEAD qui doit être recertifié exact-head avant squash merge.

## Goal UX1

À 390/430/768, conserver toutes les fonctions du dossier patient tout en supprimant les effets de desktop compressé : navigation tronquée, colonnes secondaires qui étouffent la page et overlays qui recouvrent les zones cliniques ou CTA. À 1280, préserver la densité desktop existante.

Succès observable :
- les cinq destinations patient essentielles sont visibles sans scroll horizontal caché ;
- RVG / Panoramique / Céphalométrie sont simultanément lisibles ;
- les six types du Document Studio sont immédiatement découvrables ;
- le Live Preview P6 ne recouvre plus arbitrairement le Studio ;
- CrownBot compact est accessible depuis le header et son overlay reste dans le viewport ;
- les toasts patient restent informatifs mais ne dominent ni ne bloquent CrownBot ;
- zéro overflow horizontal et zéro page error sur la matrice UX1-C 390/768/1280.

## BEFORE

Les captures initiales montraient :
- header patient trop haut sur mobile ;
- `Documents` / `Finances` hors champ à 390 ;
- sous-navigation Imagerie tronquée ;
- six types Document Studio partiellement cachés ;
- Live Preview P6 en drawer latéral recouvrant le Studio ;
- CrownBot flottant couvrant du contenu ;
- toast `Dossier à compléter` pouvant recouvrir une zone utile puis le header CrownBot.

## Référence fonctionnelle

Mobile : une tâche principale par écran. Les couches lourdes viennent par-dessus le contenu, jamais en colonne concurrente.

```text
[Menu]                     [Bot][Aide][Réglages][Notif][Sortie]
[←] NOM Patient                     [Modifier]
N° dossier · âge · téléphone
[ RDV ][ Examen ][ Document ][ Encaisser ]
[ Vue ][ Clinique ][ Imagerie ][ Documents ][ Finances ]
                 contenu métier
```

## AFTER vérifié

### UX1-A — Shell patient mobile : PASS

- Header compacté sans suppression fonctionnelle.
- `Ouvrir sur mobile` conserve une cible tactile >= 44 px.
- Les cinq destinations `Vue d’ensemble / Clinique / Imagerie / Documents / Finances` sont simultanément visibles à 390.
- Aucun scroll horizontal caché n’est requis pour découvrir une destination patient.

### UX1-B — Navigations secondaires : PASS

- Imagerie : RVG / Panoramique / Céphalométrie en grille 3 colonnes à 390/430/768.
- Document Studio : les six types P1→P6 sont visibles en grille mobile/tablette.
- Live Preview P6 : 390 plein écran utile, 768 overlay, 1280 modale centrée ; clipping nul sur la certification T2 correspondante.

### UX1-C — Couches globales : PASS visuel et comportemental sur `b73f2c7...`

Patient UX1-C Overlay Visual Certification #9 : **SUCCESS**.

Artifact :
- nom : `patient-ux1c-overlay-evidence`
- ID : `10318763556`
- digest : `sha256:f15efce3409adeb6d0581904366cade9c1fde426eb04997cdbf2ee069054cad2`

Matrice vérifiée :
- 390×844 : launcher CrownBot header visible, launcher flottant absent, overlay `366×820`, `overlayZ=1000`, `toasterZ=900`, overflow=false, pageErrors=[] ;
- 768×1024 : launcher CrownBot header visible, launcher flottant absent, overlay `744×1000`, `overlayZ=1000`, `toasterZ=900`, overflow=false, pageErrors=[] ;
- 1280×900 : launcher header absent, launcher flottant desktop visible, overlay `400×600`, overflow=false, pageErrors=[] ;
- le test échoue désormais si le toast compact passe devant CrownBot.

Autres gates observés sur `b73f2c7...` :
- Patient P7 Final Certification #1338 : SUCCESS ;
- T2 Runtime Browser Certification #2675 : SUCCESS ;
- Clinic P1 #34 : SUCCESS ;
- Clinic P2 #64 : SUCCESS ;
- Cabinet Upgrade PostgreSQL #190 : SUCCESS ;
- Settings R11 : SUCCESS ;
- Voluntary Tutorial #37 : SUCCESS ;
- Mobile Stock #56 : SUCCESS ;
- M6-I #1475 : SKIPPED attendu ;
- CI #3733 était encore en cours lors du passage au closeout documentaire et ne constitue donc pas une preuve de ce nouveau HEAD documentaire.

## P2 / human gates séparés

- `Ouvrir sur mobile` reste conservé ; aucune suppression produit automatique.
- Le wording interne `Étape P7 certifiée` n’est pas modifié sans mapping métier validé.
- Le NBA reste un toast ; aucun nouveau workflow métier n’est créé par UX1.
- Aucun déploiement Vercel n’est réalisé dans ce lot.

## Score visuel

Barème interne : lisibilité 25 %, hiérarchie 25 %, collisions/overlays 25 %, cohérence responsive 25 %.

- P6 Live Preview : **9,2/10**.
- Shell/navigation patient UX1-A/B : **8,8/10**.
- UX1-C overlays : **9,4/10** après preuve 390/768/1280 et correction du layering toast/CrownBot.
- UX1 global : **9,1/10**. Réserve principale : densité du chrome supérieur encore élevée à 390, sans collision fonctionnelle démontrée.

## Conclusion

UX1-A/B est fusionné. UX1-C est **fermé côté produit et preuve visuelle sur `b73f2c7...`**, mais la PR #468 ne doit être mergée qu’après certification exact-head du présent closeout documentaire.

## Next exact

1. Recertifier le HEAD documentaire final de PR #468.
2. Si les gates requis sont verts avec M6-I skipped attendu, vérifier mergeability + reviews/threads.
3. Squash merge PR #468.
4. Vérifier master post-merge et les éventuels workflows post-merge une fois.
