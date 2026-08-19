# R4-B — Modèles documentaires premium — Closeout

Date : 2026-08-19
Scope : Réglages → Design & Ambiance → modèles d'ordonnance / typographie documentaire.
Hors scope : Document Studio clinique, contenu médical, archivage, QR.

## Résultat

Les cinq IDs persistés sont conservés : `swiss`, `royal`, `clinical`, `modern`, `heritage`.
Le corps de prescription reste commun. Les cinq en-têtes sont désormais réellement distincts et le bilingue FR/AR ne repose plus sur une fonte inexistante.

## Audit BEFORE

- concept des cinq familles : 9.4/10 ;
- exécution visuelle : 6.9/10 ;
- différenciation : 5.8/10 ;
- vérité typographique : 4.0/10 ;
- bilingue FR/AR : 3.0/10, glyphes arabes cassés.

Preuve BEFORE : Settings Document Models Visual Audit #3, run `32203590581`, artifact `9348355380`, head `4ea5889da36bd24dd69585043d6278fa55e22f70`.

## Implémenté

- `backend/services/premium_document_headers.py` devient le moteur dédié des cinq signatures visuelles ;
- `BaseTemplate` délègue les cinq en-têtes au moteur premium ;
- choix typographiques Settings réduits à des rendus réellement disponibles et déterministes ;
- `Outfit` reste la fonte premium embarquée ;
- compatibilité backend maintenue pour les anciens IDs `playfair` et `serif` ;
- fonte arabe Unicode détectée localement sans dépendance réseau ;
- si aucune fonte arabe n'est disponible, les lignes AR sont omises plutôt que rendues avec des glyphes cassés ;
- workflow temporaire d'application supprimé avant merge.

## AFTER

Preuve visuelle finale : Settings Document Models Visual Audit #13, run `32204525445`, SUCCESS.
Head produit : `b892dba5009c7fb1ee97c26f692521d7ac2a0f46`.
Artifact : `9348657740`.
Digest : `sha256:66f2fa023118b06dc3f9d00354e90a3153d38ce86039259ac4b7ac18a0390b5c`.
Fonte arabe prouvée en CI : `ArabicFont` via `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`.
Cinq PDFs réels générés, une page chacun, même scénario clinique et même branding.

### Scores AFTER

| Modèle | BEFORE | AFTER | Verdict |
|---|---:|---:|---|
| Swiss Clinic | 7.0 | 9.2/10 | GARDER |
| Royal Elite | 7.3 | 9.1/10 | GARDER |
| Clinical Grid | 7.8 | 9.3/10 | GARDER |
| Modern Flush | 7.4 | 9.2/10 | GARDER |
| L'Héritage | 6.5 | 9.1/10 | GARDER |

Score global modèles : **9.2/10**.

Inspection : arabe lisible, aucun carré de fallback, aucun clipping/collision après correction Heritage, logo intégré, cinq signatures identifiables à faible zoom.

## Statut

R4-B visuellement certifié. Clôture R4 complète conditionnée aux derniers gates CI/T2 de la PR #174.
