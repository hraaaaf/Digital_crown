# HANDOVER — Mutuelles dentaires Digital Crown

Date : 2026-09-14.
Statut : préparation isolée, aucune intégration runtime.
Repo : `hraaaaf/Digital_crown`.
Branche : `research/mutuelles-dentaires-prep-20260914`.

## Goal
Préparer l’automatisation future des feuilles de soins dentaires CNOPS, CNSS et FAR en réutilisant Patient, Cabinet, Honoraires, Ordonnance, Acte, CatalogAct et DocumentArchive existants, avec mapping NGAP déterministe/versionné/traçable et sans risque DB.

## À lire EN PREMIER
1. `README.md`
2. `HANDOVER.md`
3. `VISUAL_REFERENCES.md`
4. `EXISTING_APP_AUDIT.md`
5. `FIELD_MATRIX.md`
6. `SOURCES.md`
7. `NGAP_POLICY.md`
8. `INSURANCE_SUBMISSION_DRAFT.md`
9. `ACT_CATALOG_LINK_STRATEGY.md`
10. `NGAP_REFERENCE_SCHEMA.md`
11. `TEMPLATE_LOCK_STATUS.md`
12. `TEST_MATRIX.md`
13. `MIGRATION_PLAN.md`

Tous sous `docs/research/mutuelles-dentaires/`.

Puis vérifier réellement master, HEAD branche, diff, PR et CI. Ne jamais croire un SHA historique par réflexe, sport très populaire chez les humains.

## État vérifié de reprise
- master observé : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc` ;
- branche avant le premier lot de reprise : `d28f81b29c1d3b588fd8a964a00ff56025a165b8` ;
- premier commit de reprise : `5332ea19170203791ec8842170a430fe144b211f` ;
- divergence initiale vérifiée : 19 ahead / 30 behind ;
- aucun PR ;
- aucun status/check CI observé sur le HEAD initial ;
- aucun runtime/UI/DB modifié.

## Livrables verrouillés
- `InsuranceSubmissionDraft` défini hors runtime ;
- provenance/type/nullabilité/invariants documentés ;
- stratégie ligne Honoraires ↔ Acte ↔ CatalogAct : historique par index contrôlé, cible `source_line_uid + catalog_act_id` ;
- schéma NGAP versionné avec `EXACT / AMBIGUOUS / NO_MATCH / OUTDATED` ;
- matrice de tests documentaires/mapping/non-régression ;
- plan de migration additive + rollback ;
- incohérence FAR de `FIELD_MATRIX.md` corrigée : FAR est bien validé cabinet.

## Templates
### CNSS
- `610-1-04`, Réf. ANAM `1.2.03.01` ;
- validation cabinet acquise ;
- PDF de référence observé comme 2 pages ;
- binaire/hash non verrouillés dans cette session.

### FAR
- `Feuille de Mutuelle FAR 2021-1` ;
- validation cabinet acquise le 2026-09-14 ;
- ne jamais la redemander sauf divergence de version/binaire ;
- binaire institutionnel/hash non verrouillés.

### CNOPS
- page institutionnelle confirme explicitement une `Feuille de soins dentaires` ;
- page dossier dentaire confirme identité assuré/bénéficiaire, INPE, cachet/signature, date, honoraires, schéma dentaire et pièces selon cas ;
- copie secondaire observée comme 2 pages ;
- téléchargement institutionnel exact en timeout dans cette session ;
- aucun SHA-256 inventé.

## Next exact
1. faire un audit final de cohérence des 13 documents ;
2. vérifier que le diff reste exclusivement `docs/research/mutuelles-dentaires/` ;
3. vérifier CI/status ;
4. si tout est cohérent, fermer le lot recherche avec un gate explicite : `READY_FOR_INTEGRATION_DESIGN` mais `NOT_READY_FOR_RUNTIME` tant que les binaires/hashes et validation métier NGAP finale ne sont pas verrouillés ;
5. ne pas créer de migration/runtime dans cette branche.

## Blocages réels
- récupération fiable des octets des templates web pour SHA-256 ;
- validation métier d’un échantillon NGAP représentatif avant activation ;
- intégration/migration volontairement hors périmètre de cette branche.

## Séquence restante
Audit final docs → diff/CI → closeout recherche → futur chantier d’intégration séparé → migration sur copie DB → tests → validation métier NGAP → activation cabinet.

## Interdits
- pas de fuzzy matching silencieux ;
- pas de second catalogue ;
- pas de données assurance inventées ;
- pas de migration réelle ici ;
- pas de déploiement.