# M6-A — Photo clinique contextuelle — Goal verrouillé

Date : 2026-08-25
Base produit exacte : `432955745da8a39fcf63277859ff4ec973722c9c`
BEFORE : run `32859436355`, artifact `9567596003`, digest `sha256:3c536022957b961b6612f05820799b5c6c4f8542971ed18b7be3f657615cfd97`

## Goal

Depuis le contexte Patient exact déjà résolu par le bridge mobile, permettre au praticien autorisé de prendre une photo clinique avec le téléphone, la vérifier avant enregistrement, puis l'archiver dans le dossier canonique du patient sans exposer ni accepter un `patient_id` côté mobile.

## Succès produit

1. Le contexte Patient affiche une action mobile-first **Photo clinique** claire et tactile.
2. L'action utilise un `input type="file"` image avec `capture="environment"` lorsque le navigateur le supporte ; le picker image reste le fallback normal.
3. La sélection n'envoie rien immédiatement : une preview locale est affichée avant enregistrement.
4. L'utilisateur peut annuler, reprendre/sélectionner une autre photo ou enregistrer.
5. Aucun blob clinique n'est conservé dans localStorage/IndexedDB par cette feature ; la preview utilise uniquement une URL objet temporaire révoquée.
6. L'upload mobile envoie seulement `context_key` + fichier. Aucun `patient_id`, nom patient ou identifiant clinique n'est ajouté à l'URL ou au multipart par le frontend.
7. Le backend résout de nouveau le contexte mobile au moment de l'upload et revalide user, cabinet, appareil, permission `patients` et patient non supprimé.
8. La photo est archivée dans la source canonique existante : `DocumentArchive` avec `DocumentType.PHOTO_CLINIQUE`. `Patient.photo_url` n'est pas détourné.
9. Le backend n'utilise jamais le nom fourni par le client comme chemin de stockage. Il génère un nom serveur.
10. Défense upload : limite 12 MiB, contenu réellement décodable par Pillow, formats sources JPEG/PNG/WEBP uniquement, limite 50 MP, réécriture serveur en JPEG haute qualité après correction d'orientation et suppression des métadonnées EXIF.
11. Un upload invalide, trop lourd, non-image, contexte non-patient, permission révoquée, patient supprimé ou appareil/session incompatible échoue explicitement sans créer de DocumentArchive.
12. En cas de backend local inaccessible, l'UI affiche une erreur française compréhensible, conserve la preview en mémoire pour permettre un nouvel essai tant que la page reste ouverte, et n'invente aucune file offline de médias.
13. Après succès, l'UI confirme **Photo clinique enregistrée dans le dossier** sans exposer le chemin disque.
14. Un événement d'audit est écrit avec user/cabinet/document, sans journaliser le contenu de l'image.

## Goal visuel

- Préserver la hiérarchie G1 et le contexte Patient existant.
- Sous la rangée `Appeler / Agenda`, ajouter une action pleine largeur **Photo clinique** avec icône caméra, 54–56 px minimum, visuellement plus mobile-first sans concurrencer le titre patient.
- Après sélection, ouvrir une bottom-sheet glass cohérente avec le design system : titre `Nouvelle photo clinique`, patient affiché, preview 4:3/contain, action secondaire `Reprendre`, CTA `Enregistrer dans le dossier`, fermeture/annulation claire.
- Ne pas afficher de patient ID, de chemin serveur ou de jargon technique.
- Après succès, conserver la preview et remplacer l'état d'action par une confirmation verte sobre + `Prendre une autre photo`.

## Accessibilité / ergonomie

- nouveaux contrôles >= 52 px ;
- focus visible ;
- image preview avec alt explicite ;
- input fichier visuellement masqué mais accessible par bouton/label ;
- reduced-motion compatible ;
- safe areas respectées ;
- 0 overflow horizontal.

## Preuves requises

### BEFORE
- 390×844, 430×932, 768×1024 ;
- photo action absente ; camera input absent ; 0 overflow / 0 runtime error.

### Backend
- exact patient context upload success ;
- archive `PHOTO_CLINIQUE` au patient exact ;
- filename client malveillant neutralisé ;
- EXIF absent après normalisation ;
- invalide / oversized / wrong resource / permission revoked / deleted patient fail-closed ;
- régression M4-A Patient context.

### AFTER
- Patient initial avec action photo : 390 / 430 / 768 ;
- preview sheet : 390 / 430 / 768 ;
- succès : 390 / 768 ;
- vérification que la requête multipart ne contient pas `patient_id` ;
- targets nouveaux >=52 ;
- 0 overflow / 0 erreur runtime ;
- comparaison BEFORE → mockup → AFTER et score visuel.

## Non-goals

- pas de galerie clinique complète dans M6-A ;
- pas de classification automatique par dent/arcade ;
- pas d'IA ;
- pas de retouche d'image ;
- pas de synchronisation offline de fichiers lourds ;
- pas de modification du profil photo patient ;
- pas de Vercel.
