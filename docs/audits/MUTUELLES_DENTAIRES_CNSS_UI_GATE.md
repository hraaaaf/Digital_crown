# Mutuelles dentaires — CNSS UI visual gate

## Goal

Relier le flux métier déjà validé à l'interface patient sans créer de nouvelle source de vérité :

`Historique patient -> Note d'honoraires canonique -> Préparer CNSS -> Revue administrative -> Validation praticien -> Génération/archivage PDF`.

## Success

Le lot UI n'est clos que si les critères observables suivants sont tous prouvés :

1. Une Note d'honoraires d'un patient CNSS expose une action explicite `Préparer CNSS` uniquement aux utilisateurs autorisés.
2. La préparation appelle le backend à partir de l'ID `DocumentArchive` de la Note d'honoraires ; aucune ligne clinique/financière n'est reconstruite côté client.
3. Les lignes Honoraires/NGAP sont affichées en lecture seule.
4. Seules les données administratives sont éditables dans la revue CNSS.
5. Les champs manquants restent visibles ; aucune identité assuré, affiliation, CIN, INPE, signature, cachet ou décision assureur n'est inventée.
6. La validation praticien est effectuée côté serveur puis la finalisation génère et archive le PDF exact.
7. Le document final apparaît dans l'historique patient.
8. BEFORE et AFTER sont capturés aux mêmes viewports `390x844`, `768x1024`, `1280x900`, sans overflow horizontal ni erreur console/page.
9. L'AFTER reste soumis à validation humaine explicite avant closeout.

## Baseline BEFORE

- SHA produit à capturer : `688242badac1a8f2ad56589ef490a19e7161980b`
- Surface : `PatientDocuments`, historique patient, carte Note d'honoraires, menu Actions ouvert.
- Attendu BEFORE : aucune action `Préparer CNSS`.

## Mockup / référence d'implémentation

### Point d'entrée

Dans le menu Actions de la carte Note d'honoraires :

- `Préparer CNSS`
- visible seulement si le patient est CNSS, le document est canonique et de type Honoraires/NOTE, et l'utilisateur a le droit comptable requis.

### Revue CNSS

Modal/panneau en trois zones :

1. **Source Honoraires vérifiée**
   - date
   - acte
   - dent(s)
   - code NGAP
   - coefficient
   - montant
   - lecture seule

2. **Données administratives CNSS**
   - données assuré requises au dossier
   - bénéficiaire
   - praticien / INPE
   - nature de demande et type de soins
   - autorisation préalable / accident seulement si renseignés
   - champs manquants explicitement signalés

3. **Actions contrôlées**
   - `Valider avec mon identité praticien`
   - après retour serveur `VALIDATED` uniquement : `Générer et archiver le PDF`

Le panneau doit préciser que la validation est une validation applicative praticien et qu'aucune signature/cachet n'est apposé automatiquement.

## Preuve exigée

- tests backend API + services existants
- tests frontend de permission/wiring
- build frontend
- capture BEFORE exacte
- capture AFTER aux mêmes viewports
- comparaison visuelle et score
- validation humaine AFTER
- CI exacte du HEAD final

## État

`IN_PROGRESS` — Goal et référence écrits ; BEFORE à certifier avant modification UI.
