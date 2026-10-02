# Logo cabinet dans les PDF — correction en attente de validation

Goal : retrouver le logo configuré du cabinet sans changer les données ni les règles de layout.

Cause : les uploads de branding utilisent `get_media_root()/clinics/...`, alors que les templates PDF consultaient seulement `backend/static/uploads/...`.

Correction : résolution commune media-first, fallback historique, refus des chemins absolus, traversées et références à un autre cabinet lorsque public_id est disponible. Application à l'en-tête, filigrane, papier à en-tête et aux deux implémentations QR.

Preuves : 20 tests ciblés passent, dont deux appels HTTP de preview utilisant la vraie génération ReportLab et une base SQLite in-memory explicitement vérifiée. Une image synthétique 83×47 est retrouvée dans les images embarquées du PDF; aucune archive supplémentaire n'est créée. Les tests couvrent aussi la priorité externe, la compatibilité historique, les chemins interdits, A4/A5, profils d'en-tête et routes QR. Le contrôle prod_safety_check passe dans la configuration test isolée; il ne certifie pas le runtime cabinet.

Visuel : before.png reconstruit le cas où l'ancien lookup ne trouve pas le logo externe (asset retiré uniquement dans les médias de test); after.png montre ce même document A5 avec le logo externe synthétique (rectangle rose). La cible est ce logo dans l'emplacement existant de l'en-tête. Le rendu conserve le titre, le corps et le pied de page; le nom retrouve l'alignement prévu lorsque le logo est présent. Ces images ne contiennent aucune donnée cabinet réelle.

Scores : EXECUTION_SCORE 7.9/10 ; ADVERSARIAL_SCORE 7.9/10 ; RETAINED_SCORE 7.9/10. Écart >0.5 : non. Plafond : validation humaine et certification complète absentes.

Gates : tests ciblés OK ; HTTP/générateur réel en fixture isolée OK (services de démarrage externes neutralisés par le conftest existant) ; comparaison visuelle inspectée OK ; validation humaine PENDING ; CI complète PENDING ; CODE_CERTIFIED PENDING ; INSTALLABLE_CERTIFIED PENDING ; activation cabinet PENDING. Runtime installé inchangé.

Statut : BLOQUÉ HUMAIN — VALIDATION CAPTURES. Next exact : recevoir la validation des captures, puis Perfection Pass, CI/certification et installation immuable. Ne pas déclarer le correctif actif dans le cabinet avant cette installation.
