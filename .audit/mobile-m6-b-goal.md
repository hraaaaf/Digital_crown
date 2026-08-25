# M6-B — Scan de documents contextuel — Goal verrouillé

Date : 2026-08-25
Base produit : `0a577f05f55a772a1b3f6d2980b18ef4e1a643fb`
BEFORE : `.audit/mobile-m6-b-before.md` / commit `dec0b8ce80d2a47b3319e1aa79a1a319f9792f82`.

## Goal

Depuis le contexte Patient exact sur mobile, permettre de photographier un document papier page par page, de contrôler les pages avant confirmation puis d'archiver un unique PDF canonique dans le dossier de ce patient, sans transmettre de `patient_id` depuis le téléphone.

## Succès observable

1. Le contexte Patient courant conserve Appeler / Agenda / Photo clinique et ajoute une action claire `Scanner un document`.
2. Le scan utilise la caméra arrière quand le navigateur le permet (`capture=environment`) avec picker image en fallback.
3. 1 à 8 pages JPEG / PNG / WebP peuvent être ajoutées ; le patient exact et le nombre de pages restent visibles pendant le flow.
4. Avant archivage, l'utilisateur peut :
   - voir la page courante ;
   - parcourir les miniatures ;
   - supprimer une page ;
   - ajouter une page ;
   - annuler le scan entier.
5. Aucun fichier n'est archivé avant `Enregistrer le PDF`.
6. L'upload mobile contient `context_key + pages[]` et jamais `patient_id`.
7. Le serveur revalide contexte / tenant / utilisateur / appareil / permission `patients` / patient non supprimé au moment de l'upload.
8. Chaque page est réellement décodée, orientation EXIF corrigée et réécrite sans métadonnées avant assemblage PDF.
9. Limites fail-closed : 8 pages maximum, 12 MiB maximum par page, 48 MiB maximum cumulés, 50 MP maximum par page.
10. Le résultat est un seul `DocumentArchive` de type `AUTRE`, titre `Document scanné`, filename généré serveur ; les images intermédiaires ne créent pas d'archives séparées.
11. Le document doit apparaître automatiquement dans la bibliothèque patient desktop existante via la source de vérité `DocumentArchive`.
12. Succès mobile explicite : `Document scanné enregistré · N page(s)` et possibilité de démarrer un nouveau scan.
13. Nouveaux contrôles visibles ≥ 52 px ; aucun overflow horizontal ni erreur runtime sur 390 / 430 / 768.

## Choix produit verrouillés

- **Pas d'OCR** dans M6-B : le lot vise une capture documentaire fiable, pas une extraction de texte fragile.
- **Pas de cloud** : traitement et archivage restent dans le serveur cabinet.
- **Pas d'auto-crop / perspective correction automatique** dans ce lot : aucune dépendance ou preuve actuelle ne justifie de complexifier le chemin critique.
- **Type `AUTRE`** : aucune classification métier ne doit être inventée à partir de l'image ; le document reste patient-scoped avec permission `patients`.
- **PDF unique multi-page** : cohérent avec la bibliothèque existante et plus simple à retrouver/télécharger qu'une pluie de JPEG indépendants.

## Non-goals

- OCR / résumé / classification automatique.
- Signature électronique.
- Partage externe.
- Synchronisation cloud.
- Modification de la bibliothèque desktop hors nécessité de compatibilité démontrée.
- Vercel.

## Preuve requise avant CLOSED

- AFTER exact-head : action → 1 page → ajout page → suppression/ordre cohérent → sauvegarde, sur 390 / 430 / 768.
- Rapport machine : contexte exact, 0 `patient_id`, nombre de pages exact, ≥52 px, 0 overflow / erreur.
- Tests backend : PDF réellement généré, 1 archive `AUTRE`, pages intermédiaires non archivées, cross-tenant/revocation/deleted patient, mauvais MIME/contenu, trop de pages, limites taille/pixels.
- Régression M6-A + M4-A.
- Build frontend + CI exact-head.
- Inspection visuelle BEFORE → mockup → AFTER et score.
