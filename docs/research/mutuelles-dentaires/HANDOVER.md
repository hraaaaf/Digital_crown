# HANDOVER — Mutuelles dentaires Digital Crown

Date : 2026-09-14.
Statut : préparation isolée, aucune intégration runtime.
Repo : `hraaaaf/Digital_crown`.
Branche de travail : `research/mutuelles-dentaires-prep-20260914`.

## Goal
Préparer l’automatisation future des feuilles de soins dentaires CNOPS, CNSS et Mutuelle des FAR en réutilisant les sources de vérité Digital Crown existantes, avec mapping NGAP déterministe et traçable, sans duplication fonctionnelle et sans risque pour la DB cabinet.

## À lire EN PREMIER à la reprise
1. `docs/research/mutuelles-dentaires/README.md`
2. `docs/research/mutuelles-dentaires/HANDOVER.md`
3. `docs/research/mutuelles-dentaires/VISUAL_REFERENCES.md`
4. `docs/research/mutuelles-dentaires/EXISTING_APP_AUDIT.md`
5. `docs/research/mutuelles-dentaires/FIELD_MATRIX.md`
6. `docs/research/mutuelles-dentaires/SOURCES.md`
7. `docs/research/mutuelles-dentaires/NGAP_POLICY.md`
8. `docs/research/mutuelles-dentaires/INSURANCE_SUBMISSION_DRAFT.md`
9. `docs/research/mutuelles-dentaires/ACT_CATALOG_LINK_STRATEGY.md`
10. `docs/research/mutuelles-dentaires/NGAP_REFERENCE_SCHEMA.md`

Puis vérifier réellement `master`, HEAD de la branche, diff, PR et CI. Ne jamais reprendre les SHA de ce fichier comme vérité actuelle sans vérification.

## État vérifié dans ce lot
- Master recroisé le 2026-09-14 : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`.
- Branche avant ce lot : `d28f81b29c1d3b588fd8a964a00ff56025a165b8`, divergente de master (19 ahead / 30 behind).
- Aucun PR et aucun status/check CI associés à ce HEAD au contrôle de reprise.
- Aucun code runtime mutuelle n’est autorisé/implémenté dans ce lot.
- Audit anti-doublon : Patient, Cabinet, Honoraires, Ordonnance, Acte, CatalogAct et DocumentArchive doivent être réutilisés.
- Dents Honoraires : source vérifiée dans `DocumentArchive.clinical_data.payments[*].dent/dents`, convention FDI.
- `PaymentItem` porte toujours `dent/dents` sur le master recroisé.
- `persist_honoraires_lines()` rapproche toujours les lignes Honoraires et les `Acte` actifs par ordre et ne persiste aucun `catalog_act_id`.
- `CatalogAct.code` reste sémantiquement mixte (`NGAP ou interne`) : ne pas l’utiliser comme NGAP fiable sans typage/provenance/version.

## Templates
### CNSS
- `610-1-04`, Réf. ANAM `1.2.03.01`.
- Référence cabinet : `https://dentiste-rabat.com/wp-content/uploads/2023/03/610-1-04_2.pdf`
- Statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.

### FAR
- Référence : `https://fr.scribd.com/document/1025435428/Feuille-de-Mutuelle-FAR-2021-1`
- Statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.
- Validation praticien déjà acquise le 2026-09-14. Ne pas la redemander sauf divergence de binaire/version.

### CNOPS
- Page institutionnelle : `https://www.cnops.org.ma/fr/infopratiques`
- Copie visuelle secondaire : `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnops-feuille-de-soins-dentaire.pdf`
- Statut : `VERIFIED_INSTITUTIONAL_PAGE / BINARY_HASH_PENDING`.

## Décisions produit verrouillées
- Pas de second moteur Honoraires.
- Pas d’Ordonnance bis.
- Pas de second catalogue d’actes/NGAP.
- `InsuranceSubmissionDraft` = DTO/adaptateur de sortie seulement.
- Cible liaison future : `source_line_uid` immuable + `catalog_act_id` nullable explicite.
- Historique : fallback contrôlé `document_archive_id + index actif`, avec fail-closed en cas de divergence.
- Données assurance Patient supplémentaires = facultatives, contextuelles, masquées par défaut.
- Toute migration future = additive, nullable/optionnelle, testée sur copie DB, aucun backfill artificiel.
- Aucun fuzzy matching silencieux acte/libellé → NGAP.
- Mapping ambigu = validation praticien.
- Aucun cachet/signature/accord assureur fabriqué.

## Livrables de conception maintenant disponibles
- `INSURANCE_SUBMISSION_DRAFT.md` : champs, provenance, invariants, unresolved fields et tests minimum.
- `ACT_CATALOG_LINK_STRATEGY.md` : compatibilité historique + cible `source_line_uid/catalog_act_id`.
- `NGAP_REFERENCE_SCHEMA.md` : mapping NGAP versionné, statuts, validités, hash et règle fail-closed.

## Next exact
Continuer sur le chemin critique documentaire, toujours hors runtime :
1. verrouiller le binaire CNOPS exact et calculer ses métadonnées/hash si récupérable ;
2. récupérer/hash les binaires CNSS/FAR depuis les références validées si techniquement accessible, sans promouvoir artificiellement leur niveau de preuve ;
3. préparer les cas de test documentaires/mapping en fixtures conceptuelles ;
4. préparer le plan de migration additive et de rollback sur copie DB ;
5. audit final anti-doublon + gate explicite ;
6. ouvrir seulement ensuite un chantier d’intégration séparé.

## Séquence restante
Templates/binaires + hash → tests documentaires → plan migration additive/rollback → audit final anti-doublon → validation métier NGAP → chantier d’intégration séparé.

## Blocages / human gates
- Validation métier FAR : NON bloquante, déjà acquise.
- Activation runtime : interdite avant gate final.
- Migration DB : interdite dans cette branche de recherche.
- Déploiement : hors périmètre et non autorisé.

## Reprise compacte
À la prochaine conversation, lire les 10 fichiers listés ci-dessus, vérifier master/branche/PR/CI, puis reprendre au `Next exact` réel. Ne pas relancer une recherche générique de formulaires CNSS/FAR ni redemander leur validation cabinet.