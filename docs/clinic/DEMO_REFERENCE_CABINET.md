# Cabinet de référence fictif Digital Crown — jeu de données durable

**Mission distincte** du lot CEPH-FAC-PARITY/P2TER-ATOMIC-ARCHIVE : cette branche ne modifie pas la PR #955. Ce jeu est destiné aux tests fonctionnels futurs et aux démonstrations ; aucune donnée de cabinet réel.

## Contenu créé

- Un compte praticien **Dr Amine Bensaid — DEMO**, email `reference-demo@digitalcrown.invalid` (domaine réservé, aucune livraison d'email).
- Un cabinet **Cabinet Digital Crown — DEMONSTRATION**, un fauteuil.
- **12 patients intégralement fictifs**, dossiers `DEMO-0001` à `DEMO-0012`, noms de fiction, aucune coordonnée téléphonique réelle.
- **36 rendez-vous** : 12 passés terminés, 12 de la semaine courante confirmés, 12 de la semaine suivante prévus. Fuseau de référence `Africa/Casablanca`; créneaux horaires locaux stockés sans offset selon le modèle applicatif.
- **36 PDF fictifs** : ordonnance, certificat, note d'honoraires par patient, générés en A5 avec mention explicite `FICTIF - DEMONSTRATION - SANS VALEUR MEDICALE`. Chaque document est inscrit dans `DocumentArchive` avec SHA-256 et chemin de média isolé.
- Script idempotent après un premier seed complet ; un état partiel entraîne un refus explicite plutôt qu'une suppression/réécriture.

## Exécution locale uniquement — non exécutée sur un cabinet

1. Préparer une **base SQLite neuve, jetable et migrée** selon la procédure normale de test du dépôt, dont le chemin absolu contient `demo`. Ne jamais pointer vers une base de cabinet ou la DB par défaut.
2. Définir `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=1`, `DATABASE_URL=sqlite:////chemin/absolu/demo-reference.db`, `DIGITALCROWN_DEMO_ROOT=/chemin/absolu/demo-reference-media` et `DIGITALCROWN_DEMO_PASSWORD` à une valeur forte générée localement d'au moins 16 caractères, différente des anciens identifiants démo. Ne jamais publier le mot de passe.
3. Exécuter `python -m scripts.seed_demo_cabinet_reference` depuis la racine du dépôt avec `reportlab` installé. Conserver la DB et le répertoire média **ensemble** pour les prochaines missions. Pour afficher les PDF via le runtime, configurer le stockage média isolé du runtime vers le répertoire racine contenant `static/archives` et vérifier le mapping réel avant usage.
4. Vérifier : 1 compte, 12 patients, 36 RDV, 36 archives, 36 PDF présents et hashes concordants. Vérifier en UI agenda et documents ; aucune validation visuelle n'est encore acquise.

**Interdictions** : pas de migration automatique de cabinet, pas de comptes/mots de passe prédéfinis en production, pas d'envoi de rappels SMS/emails depuis ce jeu, pas de génération d'actes signés, pas de copie de vraies radios ni de vraies données médicales. Les PDF sont des *maquettes*, pas des documents de soins valides.

**Statut** : script et spécification créés ; exécution réelle et contrôles de l'application **non vérifiés**. Aucun changement du HEAD `3716cc26` de la PR #955 ni de sa validation GREEN. Cette branche est un chantier distinct à revoir et tester avant intégration.
