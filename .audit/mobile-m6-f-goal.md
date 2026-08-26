# M6-F — Partage mobile contextuel — Goal

## Goal
Permettre depuis un Document mobile exact de remettre volontairement le fichier au partage natif de l’OS, sans exposer URL, token de bridge, `context_key`, nom patient ou texte prérempli.

## Succès observable
- Partage limité au contexte `document` déjà autorisé et au Blob déjà chargé.
- `navigator.share()` appelé directement depuis le geste utilisateur, sans `await` réseau préalable.
- Partage de fichier utilisé seulement si `navigator.canShare({ files: [file] })` l’accepte.
- `ShareData` contient uniquement `files` ; aucun `url`, `text` ou `title`.
- Nom partagé générique `document-digital-crown.<ext>` : aucun nom patient/original potentiellement sensible.
- Annulation native (`AbortError`) silencieuse ; autre erreur affichée sans détail technique sensible.
- Si partage fichier indisponible : fallback explicite vers `Télécharger`, sans faux succès.
- `Ouvrir`, `Télécharger`, retour et protocole M4-C préservés.
- Cibles tactiles >=48 px ; zéro overflow / erreur runtime sur 390x844, 430x932, 768x1024.

## Preuve attendue
- BEFORE exact produit : CI 32916285437 / artifact 9588310220, 390/430/768 inspectés.
- Mockup 390 px inspecté avant implémentation.
- Tests unitaires capability / nom générique / payload file-only / AbortError.
- Harness M4-C étendu : état partage supporté + fallback non supporté, aucune URL/token transmise.
- AFTER exact-head 390/430/768 comparé au BEFORE + mockup.
