# Audit anti-doublon — Digital Crown → Mutuelles dentaires

Baseline : `master` @ `5e1802901301a36fa4acf3d34adbfbde84258c18`.
Portée : lecture des audits canoniques P1/P4 + inspection ciblée du schéma courant `backend/models.py`. Aucun runtime ni migration DB exécuté dans ce lot.

## Résultat
Le futur moteur mutuelle ne doit créer ni un second moteur d’honoraires, ni une seconde ordonnance. Ces deux domaines existent déjà et produisent des documents archivables.

| Domaine existant | Preuve repo | Données/flux vérifiés | Décision future |
|---|---|---|---|
| Ordonnance | `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md` + `DOCUMENT_STUDIO_ROADMAP.md` | saisie médicament/examen, dosage, forme, posologie, contexte patient, génération `/documents/generate`, PDF, archive | REUSE : joindre/référencer l’ordonnance existante si le formulaire assureur l’exige |
| Note d’honoraires | `docs/audits/DOCUMENT_STUDIO_P4_HONORAIRES_AUDIT.md` + `DOCUMENT_STUDIO_ROADMAP.md` | `DocumentHub → AccountingStudio → AccountingStudioLegacy → useAccountingStore → useDocumentGenerator → /documents/generate → HonorairesData → create_note_honoraires() → archive → persist_honoraires_lines() → Acte / Payment` | REUSE : source financière canonique pour lignes, montants et statut |
| Patient | `backend/models.py::Patient` | `nom`, `prenom`, `date_naissance`, `sexe`, adresse/téléphones ; assurance déjà stockée via `assurance`, `assurance_privee_nom`, complémentaire | REUSE : identité clinique existante ; ne pas dupliquer |
| Cabinet / praticien | `backend/models.py::CabinetConfig` | nom cabinet/praticien, footer adresse/téléphones, `ice`, `if_`, `inpe` | REUSE : identité cabinet/praticien |
| Acte | `backend/models.py::Acte` | ID stable, patient, praticien, type, libellé, montant, date, statut financier, lien `document_archive_id` | REUSE : source acte ; mapping NGAP par identifiant/contextes structurés |
| Catalogue acte | `backend/models.py::CatalogAct` | `id`, `name`, `code` (`NGAP ou interne`), prix, spécialité | REUSE : ne pas créer un second catalogue NGAP parallèle |
| PDF / archive | `backend/models.py::DocumentArchive` + audits P1/P4 | type, version, hash, patient, fichier, métadonnées, archive | REUSE infrastructure, renderer assureur distinct |
| Paiements | audit P4 | `Payment` lié à `Acte`, statut financier, méthode explicite si encaissé | NE PAS recopier dans la feuille de soins ; seulement exposer les champs nécessaires |

## Données administratives patient : règle produit verrouillée
Les champs administratifs propres aux remboursements (CIN, n° affiliation/immatriculation/compte, qualité assuré/ayant-droit, lien avec l’assuré, organisme complémentaire détaillé, etc.) ne doivent **pas** encombrer le formulaire patient standard.

Décision cible :
- données **optionnelles** ;
- absentes visuellement du formulaire patient par défaut ;
- section activable uniquement lorsque l’utilisateur choisit d’ajouter/configurer une couverture mutuelle/assurance ou prépare une feuille de soins ;
- aucune donnée inventée ;
- absence autorisée tant qu’aucun document assureur ne l’exige ;
- réutilisées automatiquement ensuite pour les formulaires concernés.

Statut actuel vérifié : `Patient` possède déjà le type d’assurance, mais ne possède pas dans le schéma inspecté de champs structurés dédiés pour CIN, affiliation/immatriculation et relation assuré/ayant-droit.

## Compatibilité DB existante — exigence P0
Le cabinet possède déjà une base avec des patients réels. Toute intégration future doit donc être **strictement additive et rétrocompatible**.

Contraintes obligatoires :
1. aucune suppression, renommage destructif ou changement de sémantique des colonnes Patient existantes ;
2. tout nouveau champ administratif doit être `nullable`/optionnel ou bénéficier d’un défaut neutre compatible avec toutes les lignes existantes ;
3. aucune migration ne doit exiger un backfill artificiel de CIN, affiliation ou qualité assuré ;
4. les patients historiques restent valides sans données assurance supplémentaires ;
5. migration testée sur une copie représentative de DB avant activation cabinet ;
6. preuve avant/après obligatoire : nombre de patients identique, IDs conservés, champs existants inchangés, lecture/écriture des anciens dossiers intacte ;
7. rollback documenté et testé avant toute migration cabinet réelle.

Aucune migration DB n’est implémentée dans ce lot de recherche.

## Dents : gap encore à tracer
L’audit P4 exige des dent(s) structurées dans les lignes Honoraires lorsque applicable, mais le modèle SQLAlchemy `Acte` inspecté ne contient pas directement de champ dent/dents. La source réelle de cette information doit encore être tracée dans le flux frontend/document avant toute décision de schéma.

## Réutilisation obligatoire
Le futur adaptateur doit lire un snapshot cohérent des domaines existants :

```text
Patient
+ données administratives assurance optionnelles si renseignées
Cabinet / praticien
Acte + dent(s) depuis leur vraie source canonique
Note Honoraires
Ordonnance éventuelle
        ↓
InsuranceSubmissionDraft (lecture/adaptation uniquement)
```

Il est interdit de créer une table parallèle `MutuelleHonoraires`, une ordonnance bis, un catalogue d’actes indépendant ou un second solde patient pour satisfaire le formulaire.

## Gaps à verrouiller avant code
1. Données administratives patient optionnelles : CIN, n° affiliation/immatriculation/compte, qualité assuré/ayant-droit, lien avec assuré.
2. Dents : localisation exacte de la source canonique, convention de numérotation et export déterministe.
3. Actes : stratégie de lien entre `Acte` et `CatalogAct`/code NGAP sans dépendre d’un libellé libre fragile.
4. Signature/cachet : support réel et politique d’usage ; aucune génération artificielle.
5. Ordonnance FAR : rattachement au document P1 existant plutôt que duplication de lignes.
6. Version de formulaire : métadonnées `template_version`, `source_url`, `source_hash`, `verified_at`, `field_map`, `rules`.
7. Migration additive : plan et tests de non-régression DB avant toute écriture sur une base cabinet existante.

## Gate anti-doublon et anti-perte
Avant tout code mutuelle, une inspection source ciblée doit confirmer pour chaque champ : chemin modèle, type, nullabilité, source de vérité et comportement d’archive. Toute donnée déjà canonique est lue ; elle n’est pas recréée.

Avant toute migration Patient, un test sur copie de DB doit démontrer :
- `patients_before == patients_after` ;
- mêmes IDs patients ;
- aucune valeur existante perdue/modifiée ;
- nouveaux champs vides acceptés pour tous les patients historiques ;
- ouverture et modification d’un ancien dossier toujours fonctionnelles.
