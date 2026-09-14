# Plan de tests pré-intégration — Mutuelles dentaires

Statut : CONCEPTION ONLY — aucun runtime, aucune migration DB.
Date : 2026-09-14.

## Goal
Définir les preuves minimales exigées avant d’autoriser un chantier d’intégration CNOPS/CNSS/FAR + NGAP dans Digital Crown.

Succès : chaque risque structurel identifié dispose d’un test observable et d’un critère de réussite explicite.

## A. Non-régression DB existante — P0
Sur une copie représentative de la DB cabinet :

1. capturer `patients_before`, IDs et empreinte des colonnes existantes ;
2. appliquer uniquement la migration additive candidate ;
3. vérifier `patients_after == patients_before` ;
4. vérifier mêmes IDs patients ;
5. vérifier aucune valeur existante modifiée/perdue ;
6. vérifier nouveaux champs `nullable` acceptés pour tous les patients historiques ;
7. ouvrir puis modifier un dossier patient historique ;
8. exécuter et prouver le rollback.

Succès : zéro perte, zéro backfill artificiel requis, dossier historique lisible/éditable avant et après.

## B. Liaison ligne Honoraires → Acte

### Historique
- même `document_archive_id` ;
- lignes `clinical_data.payments[]` ;
- `Acte` actifs ordonnés par ID ;
- nombre de lignes = nombre d’Acte actifs ;
- date/libellé/montant concordants comme contrôles d’intégrité.

Cas :
1. alignement parfait → liaison historique admise ;
2. compte différent → `LINK_AMBIGUOUS`, fail-closed ;
3. montant/date/libellé incohérent → `LINK_AMBIGUOUS` ;
4. Acte soft-deleted → jamais rematché.

### Cible additive
1. création ligne → `source_line_uid` unique ;
2. édition contenu/prix/date → UID conservé ;
3. réordonnancement → UID conservé ;
4. suppression → UID historique conservé ;
5. nouvelle ligne après suppression → nouvel UID ;
6. propagation snapshot Honoraires ↔ Acte exacte.

## C. Liaison CatalogAct
1. sélection depuis catalogue → `catalog_act_id` explicite conservé ;
2. saisie libre → `catalog_act_id = null` ;
3. libellé ressemblant à un acte catalogue → aucun rattachement implicite ;
4. `catalog_act_id` inexistant/inactif → blocage ;
5. modification volontaire du rattachement → nouveau snapshot traçable ;
6. historique sans `catalog_act_id` → aucun NGAP automatique.

## D. Dents / FDI
1. une dent → même valeur FDI dans `InsuranceSubmissionDraft` ;
2. plusieurs dents → liste normalisée/déterministe ;
3. dent temporaire valide → acceptée ;
4. valeur hors FDI autorisé → rejet ;
5. ligne sans dent → aucune dent inventée ;
6. `dent` texte en conflit avec `dents[]` → `dents[]` structuré prévaut selon la politique existante ;
7. aucune extraction depuis le libellé de l’acte.

## E. NGAP — fail-closed
1. `CatalogAct.code` de type INTERNAL → jamais émis comme NGAP ;
2. mapping ACTIVE, source/hash/version valides, une seule règle → `EXACT` ;
3. deux règles applicables → `AMBIGUOUS` ;
4. aucun mapping → `NO_MATCH` ;
5. mapping expiré/superseded/unverified → `OUTDATED` ;
6. source/hash manquants → mapping non activable ;
7. règle multi-actes → résultat conforme au jeu de règles versionné ;
8. mêmes entrées + même référentiel → même résultat ;
9. nouvelle version référentiel → ancien document conserve l’ancienne version/hash.

Succès : seul `EXACT` peut préremplir ; validation finale praticien reste explicite.

## F. InsuranceSubmissionDraft
1. identité Patient/Cabinet présente → AUTO ;
2. CIN/affiliation manquants → `unresolved_fields`, jamais inventés ;
3. assuré distinct → aucune déduction silencieuse ;
4. document Honoraires source obligatoire ;
5. pièce Ordonnance existante → référence P1, aucune duplication ;
6. pièce radio absente mais requise par règle → `MISSING/MANUAL_REQUIRED` ;
7. champ assureur → laissé vierge ;
8. signature/cachet sans actif réel → blocage ou `SIGNATURE_REQUIRED` ;
9. même snapshot + mêmes versions → même DTO hors timestamp technique.

## G. Templates assureurs
Pour chaque CNOPS/CNSS/FAR :
1. organisme et référence exacts ;
2. provenance ;
3. nombre de pages ;
4. hash SHA-256 si le binaire exact est récupérable ;
5. statut `CABINET_REFERENCE`, `INSTITUTIONAL_PAGE`, `PRIMARY` selon preuve réelle ;
6. champ source → coordonnées/template vérifiées ;
7. aucun champ clinique/administratif écrit dans une zone organisme ;
8. comparaison visuelle avec la référence validée sur toutes les pages.

Un hash indisponible n’est jamais inventé : le renderer final reste bloqué tant que le niveau de preuve requis n’est pas atteint.

## H. Tests de rendu futurs — UI/PDF
Quand le chantier d’intégration sera autorisé :
- BEFORE de chaque template ;
- Goal visuel écrit ;
- rendu avec jeu de données synthétique contrôlé ;
- AFTER aux mêmes dimensions/pages ;
- comparaison positionnelle ;
- inspection de toutes les pages ;
- score visuel ;
- zéro texte coupé, chevauchement, mauvais champ ou page manquante.

## I. Scénarios métier minimaux
- consultation simple ;
- soin conservateur 1 dent ;
- endodontie avec radiographies requises ;
- extraction ;
- prothèse multi-dents ;
- acte libre non mappé ;
- deux actes même séance ;
- bénéficiaire différent de l’assuré ;
- patient historique sans données mutuelle ;
- mapping NGAP ambigu ;
- référence NGAP expirée.

## Gate final avant chantier runtime
Tous les points P0 et fail-closed doivent être verts. Les templates activés doivent posséder le niveau de preuve réellement exigé par le projet, et un échantillon représentatif de feuilles doit être relu par un chirurgien-dentiste connaissant AMO/NGAP.

Ce fichier ne constitue pas une autorisation d’intégration.