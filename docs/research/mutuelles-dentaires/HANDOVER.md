# HANDOVER — Mutuelles dentaires Digital Crown

Date : 2026-09-14.
Statut : préparation isolée, aucune intégration runtime.
Repo : `hraaaaf/Digital_crown`.
Branche de travail : `research/mutuelles-dentaires-prep-20260914`.

## Goal
Préparer l’automatisation future des feuilles de soins dentaires CNOPS, CNSS et Mutuelle des FAR en réutilisant les sources de vérité Digital Crown existantes, avec mapping NGAP déterministe et traçable, sans duplication fonctionnelle et sans risque pour la DB cabinet.

## À lire EN PREMIER à la reprise
1. `docs/research/mutuelles-dentaires/README.md` — canonical principal.
2. `docs/research/mutuelles-dentaires/HANDOVER.md` — ce handover.
3. `docs/research/mutuelles-dentaires/VISUAL_REFERENCES.md` — modèles CNSS/FAR/CNOPS.
4. `docs/research/mutuelles-dentaires/EXISTING_APP_AUDIT.md`.
5. `docs/research/mutuelles-dentaires/FIELD_MATRIX.md`.
6. `docs/research/mutuelles-dentaires/SOURCES.md`.
7. `docs/research/mutuelles-dentaires/NGAP_POLICY.md`.

Puis vérifier réellement `master`, HEAD de la branche, diff, PR et CI. Ne jamais reprendre les SHA de ce fichier comme vérité actuelle sans vérification.

## État vérifié avant handover
- Master observé le 2026-09-14 : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`.
- La branche research a été créée initialement depuis une baseline antérieure ; elle ne doit pas être mergée mécaniquement sans rebase/contrôle de cohérence avec le master courant.
- Aucun code runtime mutuelle n’est autorisé/implémenté dans ce lot.
- Audit anti-doublon : Patient, Cabinet, Honoraires, Ordonnance, Acte, CatalogAct et DocumentArchive doivent être réutilisés.
- Dents Honoraires : source vérifiée dans le snapshot `DocumentArchive.clinical_data.payments[*].dent/dents`, convention FDI.
- `Acte` ne porte actuellement ni dent(s) ni `catalog_act_id`.
- `CatalogAct.code` existe mais sa sémantique est mixte (`NGAP ou interne`) : ne pas l’utiliser comme NGAP fiable sans typage/provenance/version.

## Templates
### CNSS
- `610-1-04`, Réf. ANAM `1.2.03.01`.
- Référence : `https://dentiste-rabat.com/wp-content/uploads/2023/03/610-1-04_2.pdf`
- Statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.

### FAR
- Référence : `https://fr.scribd.com/document/1025435428/Feuille-de-Mutuelle-FAR-2021-1`
- Statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.
- Le praticien a confirmé qu’il avait déjà validé ce modèle. Ne pas redemander cette validation sauf divergence de binaire/version.

### CNOPS
- Page institutionnelle : `https://www.cnops.org.ma/fr/infopratiques`
- Copie visuelle secondaire : `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnops-feuille-de-soins-dentaire.pdf`
- Statut : `VERIFIED_INSTITUTIONAL_PAGE / BINARY_HASH_PENDING`.

## Décisions produit verrouillées
- Pas de second moteur Honoraires.
- Pas d’Ordonnance bis.
- Pas de second catalogue d’actes/NGAP.
- `InsuranceSubmissionDraft` futur = DTO/adaptateur de sortie seulement.
- Données assurance Patient supplémentaires = facultatives, contextuelles, masquées par défaut.
- Toute migration Patient future = additive, nullable/optionnelle, testée sur copie DB, aucun backfill artificiel.
- Aucun fuzzy matching silencieux acte/libellé → NGAP.
- Mapping ambigu = validation praticien.
- Aucun cachet/signature/accord assureur fabriqué.

## Next exact
Préparer le contrat de données futur `InsuranceSubmissionDraft` à partir des sources existantes, mais rester hors runtime :
1. définir les champs et leur provenance exacte ;
2. définir la stratégie stable ligne Honoraires/Acte ↔ `CatalogAct` sans modifier encore le schéma ;
3. spécifier le typage NGAP/interne + provenance/version/validité ;
4. verrouiller le binaire CNOPS et ses métadonnées si récupérable ;
5. documenter les métadonnées/hash des références CNSS/FAR si le binaire est récupérable ;
6. préparer les tests de mapping et de non-régression DB ;
7. ne commencer l’intégration applicative qu’après audit/gate explicite.

## Séquence restante
Contrat DTO → stratégie liaison actes/catalogue → référentiel NGAP versionné → verrouillage binaires/templates → tests documentaires → plan migration additive → audit final anti-doublon → seulement ensuite chantier d’intégration séparé.

## Prompt de reprise
Copier le prompt ci-dessous dans une nouvelle conversation :

```text
Nous reprenons le chantier Digital Crown « Mutuelles dentaires ».

Repo GitHub : hraaaaf/Digital_crown
Branche de préparation : research/mutuelles-dentaires-prep-20260914

LIS EN PREMIER ET INTÉGRALEMENT :
1. docs/research/mutuelles-dentaires/README.md
2. docs/research/mutuelles-dentaires/HANDOVER.md
3. docs/research/mutuelles-dentaires/VISUAL_REFERENCES.md
4. docs/research/mutuelles-dentaires/EXISTING_APP_AUDIT.md
5. docs/research/mutuelles-dentaires/FIELD_MATRIX.md
6. docs/research/mutuelles-dentaires/SOURCES.md
7. docs/research/mutuelles-dentaires/NGAP_POLICY.md

Ensuite vérifie réellement master, HEAD de la branche, diff, PR/CI éventuelles. Ne suppose aucun SHA du handover encore courant.

Goal : préparer l’automatisation des feuilles de soins dentaires CNOPS, CNSS et Mutuelle des FAR en réutilisant Patient, Cabinet, Actes, Honoraires, Ordonnance, CatalogAct et DocumentArchive existants, avec NGAP déterministe/versionné/traçable, sans duplication et sans risque pour la DB cabinet.

Contraintes : NE PAS intégrer dans l’app pour le moment. Tout reste sur la branche de recherche/documentation. Avant toute future intégration, auditer l’existant pour éviter de refaire ce qui existe déjà.

Templates déjà verrouillés métier :
- CNSS 610-1-04 = VERIFIED_CABINET_REFERENCE.
- FAR Feuille de Mutuelle FAR 2021-1 = VERIFIED_CABINET_REFERENCE. Ne redemande pas sa validation sauf divergence de version.
- CNOPS = page institutionnelle identifiée, binaire/hash encore à verrouiller.

Next exact : préparer le contrat de données InsuranceSubmissionDraft hors runtime, préciser la liaison stable Honoraires/Acte ↔ CatalogAct, puis le schéma de référentiel NGAP versionné. Continuer ensuite automatiquement sur le chemin critique documentaire tant qu’aucun human gate réel n’est rencontré.
```
