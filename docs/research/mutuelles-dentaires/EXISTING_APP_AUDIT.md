# Audit anti-doublon — Digital Crown → Mutuelles dentaires

Baseline : `master` @ `5e1802901301a36fa4acf3d34adbfbde84258c18`.
Portée : audits canoniques P1/P4 + inspection ciblée des modèles, schémas Documents, route `/documents/generate` et persistance Honoraires. Aucun runtime ni migration DB exécuté dans ce lot.

## Résultat
Le futur moteur mutuelle ne doit créer ni second moteur d’honoraires, ni seconde ordonnance, ni second catalogue d’actes. Les données utiles existent déjà, mais deux liaisons structurées manquent aujourd’hui : `Acte → dent(s)` et `Acte → CatalogAct`.

| Domaine existant | Preuve repo | Données/flux vérifiés | Décision future |
|---|---|---|---|
| Ordonnance | `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md` | médicament/examen, dosage, forme, posologie, contexte patient, PDF/archive | REUSE |
| Note d’honoraires | audit P4 + `backend/routers/documents.py` | génération, archive, persistance Acte/Payment | REUSE : source financière canonique |
| Patient | `backend/models.py::Patient` | nom, prénom, naissance, sexe, coordonnées, type d’assurance | REUSE ; données mutuelle supplémentaires optionnelles |
| Cabinet / praticien | `backend/models.py::CabinetConfig` | identité, adresse/téléphones, `ice`, `if_`, `inpe` | REUSE |
| Contrat Honoraires | `backend/schemas/documents.py::PaymentItem` | `dent` + `dents` structurées dans chaque ligne | REUSE |
| Archive documentaire | `backend/models.py::DocumentArchive.clinical_data` + `documents.py` | `req.data` complet archivé comme JSON | SOURCE CANONIQUE actuelle des dent(s) d’une note Honoraires |
| Acte dérivé | `backend/services/honoraires_persistence.py` | libellé, montant, date, statut, praticien, document archive | REUSE mais dent(s) non matérialisées dans `Acte` |
| Catalogue acte | `backend/models.py::CatalogAct` | `id`, `name`, `code` (`NGAP ou interne`), prix, spécialité | REUSE ; ne pas créer un second catalogue |
| Paiements | P4 + `honoraires_persistence.py` | Payment exact par Acte quand PAYE | REUSE, hors mapping mutuelle |

## Dents — source canonique verrouillée
### Ce qui existe
`PaymentItem` contient déjà :
- `dent: Optional[str]` ;
- `dents: Optional[List[str]]`.

Les données Honoraires reçues par `/documents/generate` sont archivées via :

```text
archive_service.archive_document(... clinical_data=req.data ...)
```

`DocumentArchive.clinical_data` est un champ JSON. Pour une note Honoraires archivée, la dentition de la ligne reste donc récupérable dans le snapshot documentaire.

Le schéma Devis valide en outre la numérotation FDI :
- adulte : 11–18, 21–28, 31–38, 41–48 ;
- temporaire : 51–55, 61–65, 71–75, 81–85.

### Ce qui est perdu dans le miroir `Acte`
`persist_honoraires_lines()` reçoit le payload complet, mais ne persiste dans `Acte` que les données comptables/cliniques générales : libellé, montant, date, statut, praticien et `document_archive_id`.

Il ne copie actuellement ni `dent`, ni `dents` dans `Acte`.

**Décision :** pour préparer une feuille mutuelle issue d’une note Honoraires, la source actuelle des dent(s) doit être `DocumentArchive.clinical_data.payments[*].dent/dents`, reliée aux Acte dérivés par `document_archive_id` + ordre de ligne. Ne pas inventer une seconde dentition ni parser le libellé.

Le lien par ordre de ligne est acceptable comme mécanisme de lecture de l’existant, mais reste moins robuste qu’un identifiant de ligne stable. Avant intégration, il faudra décider si le snapshot documentaire suffit ou si un identifiant de ligne immuable doit être ajouté de façon additive.

## Acte ↔ catalogue ↔ NGAP — gap structuré verrouillé
`CatalogAct.code` existe déjà et peut contenir un code NGAP **ou interne**.

Cependant :
- `Acte` n’a pas de `catalog_act_id` ;
- `persist_honoraires_lines()` ne persiste aucun ID de catalogue ;
- le flux Honoraires persiste essentiellement le `libelle` ;
- aucune preuve d’un identifiant catalogue stable conservé dans la ligne Honoraires actuelle n’a été trouvée dans cet audit ciblé.

**Conséquence :** un mapping NGAP automatique ne peut pas considérer `Acte.libelle` comme une clé métier fiable, et ne peut pas considérer tout `CatalogAct.code` comme NGAP sans typer sa provenance.

Architecture recommandée avant activation :
1. réutiliser `CatalogAct` comme catalogue unique ;
2. distinguer explicitement code interne / code NGAP et sa version/provenance ;
3. introduire seulement si nécessaire un lien additif stable entre ligne document/Acte et `CatalogAct` ;
4. conserver le code NGAP effectivement utilisé dans le snapshot du document mutuelle pour réimpression historique.

Aucun de ces changements n’est implémenté dans ce lot.

## Données administratives patient
Les données propres aux remboursements (CIN, affiliation/immatriculation/compte, qualité assuré/ayant-droit, lien avec assuré...) restent :
- optionnelles ;
- absentes du formulaire Patient standard par défaut ;
- affichées uniquement dans une section assurance/mutuelle ou lors de la préparation d’une feuille ;
- jamais inventées ;
- réutilisables ensuite si renseignées.

Le schéma `Patient` inspecté possède déjà le type d’assurance mais pas de champs structurés dédiés CIN/affiliation/relation assuré-bénéficiaire.

## Compatibilité DB existante — P0
Toute évolution future est strictement additive et rétrocompatible :
1. aucune suppression/renommage destructif de colonne existante ;
2. nouveaux champs nullable/optionnels ;
3. aucun backfill artificiel obligatoire ;
4. patients historiques toujours valides ;
5. migration testée sur copie représentative de DB ;
6. même nombre de patients, mêmes IDs, aucune valeur existante perdue/modifiée ;
7. lecture/écriture anciens dossiers intacte ;
8. rollback documenté et testé.

Aucune migration DB n’est implémentée dans ce lot.

## Réutilisation obligatoire
```text
Patient
+ données assurance optionnelles
Cabinet / praticien
DocumentArchive Honoraires
  └─ payments[*].dent/dents + acte + montant
Acte dérivé + Payment
CatalogAct unique
Ordonnance éventuelle
        ↓
InsuranceSubmissionDraft (lecture/adaptation uniquement)
```

Interdits : `MutuelleHonoraires`, ordonnance bis, second catalogue d’actes, second solde patient, parsing silencieux libellé→NGAP.

## Gaps restant avant code
1. Définir le mécanisme stable ligne Honoraires/Acte ↔ `CatalogAct` sans dépendre d’un libellé libre.
2. Typer/versionner clairement `CatalogAct.code` pour distinguer NGAP et code interne.
3. Signature/cachet : support réel et politique d’usage.
4. Ordonnance FAR : rattachement à P1.
5. Templates : `template_version`, source, hash, field map et règles.
6. Migration additive : plan et tests de non-régression DB.
7. Validation métier FAR et verrouillage CNOPS exact.

## Gate anti-doublon / anti-perte
Avant tout code mutuelle : source de vérité de chaque champ, type, nullabilité, provenance et archivage doivent être explicites. Les données déjà canoniques sont lues, jamais recréées.
