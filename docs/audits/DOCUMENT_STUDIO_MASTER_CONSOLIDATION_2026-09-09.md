# Document Studio — Master Consolidation 2026-09-09

## Goal
Rebaseliner Document Studio sur le `master` courant et ne porter que les deltas encore absents et utiles, sans réintroduire les branches historiques divergentes.

## Baseline vérifiée
- repository: `hraaaaf/Digital_crown`
- master initial: `6301f737f59e1f5c6c0e1e79402fbd5270637617`
- consolidation fonctionnelle: PR `#379`
- merge #379 sur master: `815a269a92ccd95fa51ce68b3338dfa4392d3f9b`
- certification PDF finale: PR `#380`

## Deltas consolidés
- Prescription: persistance fail-visible, rollback + propagation, suggestions strictement local-first sans fallback HTTP `medicament.ma`.
- Certificat: ligne de signature conservée, nom praticien conservé, mention imprimée `Signature manuscrite du praticien` retirée.
- Devis: validation `items ↔ teeth_data` avec rejet dent/traitement orphelin et divergence de prix.
- Tests de régression dédiés pour ces contrats.

## Nettoyage des branches historiques
- #18 CLOSED sans merge après port utile.
- #77 CLOSED sans merge après port/supersession.
- #101 CLOSED comme superseded.
- #336 CLOSED comme superseded.
- #353 CLOSED après port utile.
- #90/#95/#96 déjà fermées et superseded par le master courant.
- #97 déplacée vers Scientific Core / MEDICAL GATE.
- #1 reste hors périmètre Document Studio et nécessite une réconciliation multi-domaines séparée.

## Preuves exact-head
### Consolidation #379
HEAD `bec1c725004243ba99c2f915d59ad9a9449221b4`
- CI run #2879: SUCCESS.
- T2 Runtime Browser Certification #1910: SUCCESS.
- Catalog Connected Truth Certification #1011: SUCCESS.
- PR #379 mergée sur `master` en `815a269a92ccd95fa51ce68b3338dfa4392d3f9b`.

### Certification PDF #380
Premier HEAD de preuve `b6dbcbb8fd41e33e2308152f3754033e12027750` :
- CI run #2896: SUCCESS.
- T2 Runtime Browser Certification #1925: SUCCESS.
- M6-I Biometric Passkey Certification #725: SKIPPED, hors scope.

Le test `backend/tests/test_document_studio_pdf_generation_certification.py` génère réellement :
1. un Certificat via `CertificatGenerator.generate()` ;
2. un Devis via `AccountingGenerator.generate_devis()` avec `DevisData` cohérent `items ↔ teeth_data`.

Pour chaque sortie, le test exige : fichier présent, en-tête `%PDF-`, taille > 1 000 octets et marqueur `%%EOF` dans la fin du fichier.

## UI/UX
Aucun fichier UI n'a été modifié par #379/#380. Le cycle BEFORE/AFTER visuel n'est donc pas applicable à ce lot.

## Gate final
Le présent commit de closeout modifie le HEAD de #380. Le chantier n'est déclaré CLOSED qu'après CI exact-head de ce commit puis merge #380 et vérification post-merge de `master`.

## État
**FINAL CI GATE — preuves fonctionnelles et PDF acquises sur le HEAD précédent ; closeout canonique ajouté, CI exact-head finale requise avant merge.**
