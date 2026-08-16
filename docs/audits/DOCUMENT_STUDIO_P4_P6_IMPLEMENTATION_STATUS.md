# Document Studio — P4/P5/P6 : statut d’implémentation

## Baseline

- Branche : `agent/p4-p6-audit-baselines`.
- PR : #79.
- Base : `master` `026f78290cda53ea1b07ba5e8bfd39836448d6ce`.
- Audits baseline :
  - `DOCUMENT_STUDIO_P4_HONORAIRES_AUDIT.md` ;
  - `DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md` ;
  - `DOCUMENT_STUDIO_P6_DOCUMENT_LIBRE_AUDIT.md`.

Les audits restent la photographie des défauts initiaux. Le présent fichier décrit ce qui a été corrigé ensuite.

## P4 — Note Honoraires

### Implémenté sur PR #79

- `payment_status` fermé sur `EN_ATTENTE | PAYE | PARTIEL`, avec `PARTIEL` toujours refusé par le flux documentaire faute de montant encaissé explicite.
- Note vide et acte vide refusés au contrat request.
- Montant Honoraires : numérique, fini, strictement positif, plafond 1 000 000 MAD par ligne.
- Validation invariant répétée avant génération PDF.
- Persistance Acte/Payment revalide les lignes avant toute écriture.
- Pour `PAYE`, le mode de règlement doit être explicitement fourni ; aucun fallback silencieux vers espèces.
- Pour `EN_ATTENTE`, aucun mode de règlement n’est requis puisqu’aucun encaissement n’est créé.
- `PAYE` conserve l’allocation historique exacte : un `Payment` positif lié à chaque `Acte`.
- Réconciliation exacte des échéances d’une note globale conservée.
- Tests ciblés ajoutés aux niveaux request, pré-PDF et persistance.

### Dépendances / gates encore ouverts

- P3 → P4 explicite et nettoyage partagé du lifecycle doivent être réconciliés avec la PR P3 #77 avant merge final ; #77 est toujours draft et non mergée.
- La suggestion financière RDV générique est déjà retirée dans #77 ; éviter une correction concurrente sur la branche P4.
- Suggestion radio par mots-clés : reste à arbitrer/neutraliser lors de la réconciliation partagée P3/P4.
- Suite complète, build, runtime authentifié, PDF réel et certification financière restent non exécutés sur ce head.

## P5 — Suivi Paiement

### Implémenté sur PR #79

- Contrat `InstallmentPlanCreate` fail-closed : titre borné, total fini/positif, au moins une échéance, montants finis/positifs, statuts fermés.
- Réconciliation exacte au centime imposée serveur pour création et preview.
- Chemin documentaire direct `echeancier` sans `plan_id` durci avec titre, dates explicites, montants valides et réconciliation exacte.
- Endpoint `/installments/patient/{patient_id}/latest` explicite et tri serveur déterministe.
- Liste patient ordonnée explicitement.
- Échéance `PAYE` toujours non réouvrable/non rechiffrable sans contrepassation.
- Suppression d’un plan contenant une échéance PAYE refusée.
- UI P5 transformée en lifecycle explicite : `brouillon équilibré → enregistrer le plan → encaisser une échéance persistée`.
- Ancien checkbox local « Réglé » supprimé : il ne peut plus simuler un encaissement.
- Encaissement désactivé tant que le praticien n’a pas choisi explicitement Espèces/Carte/Chèque/Virement.
- Montants d’un plan persisté figés ; restructuration via nouveau plan.
- Dates envoyées au contrat backend sous forme datetime explicite.
- Résumé visible : total planifié, payé, restant.
- WhatsApp reste une ouverture manuelle explicite, aucun envoi automatique.
- Tableau rendu scrollable horizontalement sur écrans étroits ; validation visuelle réelle encore requise.
- Tests schema, route et frontend ajoutés/alignés.

### Dépendances / gates encore ouverts

- Le chargement historique P5 dans le store comptable global de `DocumentHub` ne doit pas être supprimé en parallèle avant réconciliation de la PR P3 #77, qui modifie déjà l’isolation P3. P5 possède désormais son propre endpoint/latest et n’en dépend plus fonctionnellement.
- Suite complète, build, runtime authentifié et certification financière restent non exécutés sur ce head.

## P6 — Document Libre

Aucun nouveau défaut P0 statique démontré pendant cette passe. Aucun changement produit n’a été ajouté uniquement pour « faire du code ».

Engineering existant conservé : validation fail-closed, markup allowlisté, PDF long/multipage, dirty-state, permission clinique, impression fraîche, archive/réouverture.

### Gates encore ouverts

- régression frontend/backend/PDF réelle ;
- runtime authentifié ;
- inspection PDF A4/A5, long, tableaux, caractères spéciaux ;
- responsive 1440/768/390 et accessibilité clavier ;
- amélioration WYSIWYG/templates reste une option produit, pas une condition de sécurité.

## CI / preuve

Les runs GitHub observés sur PR #79 échouent avant allocation/exécution des steps (`steps=null`). Ils ne constituent ni un échec applicatif ni une validation.

Aucun statut `production ready`, aucune certification financière et aucun PASS runtime ne sont revendiqués tant que les gates ci-dessus ne sont pas réellement exécutés.
