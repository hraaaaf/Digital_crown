# P4 — Note Honoraires — certification finale engineering/runtime

Date : 2026-09-09
PR : #386
HEAD produit certifié : `99c63b1247448805360e949d6da745afa53ba340`
Base : `master@78497c9b0390e8586e5dddbf13f31d0c10387572`

## Verdict

**P4 engineering/runtime automatisé : FERMÉ.**

Ce verdict ne constitue pas une certification comptable, réglementaire ou financière externe. La compensation DB/fichier reste applicative et non ACID distribuée.

## Preuves exécutées

### T2 Runtime Browser
Run `34413159443` : **success**.

Étapes vertes :
- PDF runtime strict ;
- réconciliation persistée P3/P4/P5 ;
- matrice navigateur authentifiée ;
- impression navigateur + fraîcheur PDF.

Artifact `t2-browser-evidence` id `10128130682` :
- `financial-probe.json` : PASS ;
- `pdf-probe.json` : PASS ;
- `output-gates.json` : PASS ;
- `results.json` / `scores.json` : PASS.

### P4 financier persisté

`financial-probe.json` démontre :
- note vide -> 422 ;
- montant 0 -> 422 ;
- PAYE sans mode de règlement -> 422 ;
- PARTIEL implicite -> 422 ;
- aucun de ces refus ne mute Document/Acte/Payment/plan ;
- EN_ATTENTE : un Document + un Acte, aucun Payment ;
- PAYE : un Document + un Acte + un Payment exact de 888 MAD ;
- Payment lié à un `acte_id` ;
- archive retrouvée depuis le dossier patient ;
- réhydratation `payment_status=PAYE` ;
- réhydratation `is_accounted=true`.

### Multi-actes PAYE

`backend/tests/test_honoraires_payment_allocation_p2f.py`, exécuté dans la full-suite backend CI :
- 2 Actes ;
- 2 Payments ;
- montants exacts 400 + 2500 MAD ;
- chaque Payment lié à l'Acte correspondant ;
- somme exacte 2900 MAD ;
- mode TPE persisté comme CARTE.

### Note globale / échéances

`backend/tests/test_honoraires_installment_contract_p2e.py`, exécuté dans la full-suite backend CI :
- 333.33 + 333.33 + 333.34 accepté pour 1000 MAD ;
- sous-total refusé ;
- sur-total refusé ;
- échéance non positive refusée ;
- une note non globale n'impose pas cette réconciliation.

### CI principal

Run `34413159336` : **success**.

- backend : `python -m pytest backend/tests -q --maxfail=1` ;
- frontend : `npm test` ;
- build : `npm run build` ;
- garde production négatif : success ;
- M4-A/B/C : success.

## PDF et impression

Le chemin `/documents/generate` route explicitement `note` / `honoraires` vers `doc_factory.create_note_honoraires(...)`.

Le générateur dédié `AccountingGenerator.generate_note()` produit la NOTE D'HONORAIRES et son tableau Acte / Dent / Paiement / Honoraires, ainsi que l'échéancier lorsqu'il existe.

L'UI Honoraires utilise le même `useDocumentGenerator` / `generator.handleGenerate` et le même `StudioFooter` que le chemin d'impression navigateur T2 certifié.

Le probe PDF T2 vérifie serving HTTP `application/pdf` et signature `%PDF`. L'inspection visuelle humaine du contenu PDF reste une validation distincte et ne doit pas être confondue avec le gate engineering/runtime.

## Responsive / UX runtime

`scores.json` : Note Honoraires = **10/10 technique**, verte sur 5 exécutions :
- 390×844 light ;
- 430×932 light ;
- 768×1024 light ;
- 1280×900 light ;
- 1280×900 dark.

Sections : navigation, éditeur/contenu, actions, absence d'overflow horizontal, stabilité runtime, hiérarchie, preview = vertes.

Limite UX : ce score est un score de gates techniques automatisés, pas une note esthétique humaine.

## Lot édition / Historique déjà certifié

PR #384 + #385 couvrent séparément :
- remplacement d'archive lors d'une édition, sans append ;
- réconciliation Acte/Payment et dates ;
- corbeille/restauration ;
- hydratation financière à la réouverture ;
- préfixe arabe praticien ;
- menu Historique sans overlap/clipping ;
- polish final du dropdown.

## Conclusion

Le périmètre P4 exécutable par l'engineering automatisé est fermé sur le HEAD produit ci-dessus.

Restent hors de ce verdict :
- validation comptable/réglementaire humaine si elle est exigée par le cabinet ou une autorité ;
- inspection humaine esthétique d'un PDF cabinet réel ;
- certification production sur un environnement cabinet réel.

Ces éléments sont des gates externes distincts et ne rouvrent pas l'engineering P4 sauf défaut observé.
