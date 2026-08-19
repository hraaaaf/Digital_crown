# Patient P2 — Vue d’ensemble / Patient Journey

## Goal
Faire de la Vue d’ensemble la colonne vertébrale factuelle et actionnable du dossier Patient, sans dupliquer les sources ni produire de conclusion clinique automatique.

## Baseline visuelle
Baseline = P1 AFTER, immédiatement avant P2, sur le merge `79394cc823a3c91801f841804f31656bdb8e1f32`.

- Run : `32201889501` (#6)
- Artifact : `9347877116`
- Digest : `sha256:0e1c42bc50b64c12b9f13da25483dbbe52cc963cdcfed62dd9afd064c5b3b8e4`
- Viewports : 390x844, 430x932, 768x1024, 1280x900

Constats baseline :
- `FlashSummary` ajoute au-dessus du Journey un résumé algorithmique opaque (`clinical_summary`, `risk_level`) sans provenance visible.
- Le Journey affiche `0/0` lorsqu’aucun Master Plan n’est enregistré.
- Le Treatment Plan depuis la timeline ouvre encore Documents (`tab=admin`).
- Les cartes de résumé ne donnent pas toutes une source et une date de référence explicites.

## Contrat de vérité
Le backend Journey reste un agrégateur en lecture seule. Les tables sources demeurent autoritatives.

| Information | Source canonique | Règle P2 |
|---|---|---|
| Prochain RDV | Appointment | date/id réels, lien Agenda |
| Plan actif | TreatmentMasterPlan + TreatmentPlanStep | aucune étape => « Aucun plan enregistré », jamais `0/0` présenté comme activité |
| Prochaine action | Appointment puis première TreatmentPlanStep PENDING par `order_index` | règle opérationnelle déterministe, jamais recommandation clinique |
| Situation financière | Acte + Payment, avec `has_billing_data` | absence de base facturée => « Solde indéterminé », jamais faux `0 MAD` |
| Dernier document | DocumentArchive | date réelle |
| Timeline | 9 sources Journey existantes | chaque événement conserve source, ref_id, date et cible réelle |

## Suppression P2
`FlashSummary` doit disparaître de la Vue d’ensemble. Son endpoint actuel agrège des heuristiques (`risk_level`, alertes, tendances) et n’est pas une source de vérité nécessaire au Journey.

Le toast NBA ne doit pas être utilisé comme résumé P2 ni comme source de prochaine action. La frontière P0-I reste inchangée.

## Wireframe cible

```text
VUE D’ENSEMBLE

┌──────────────────────────────────────────────────────────────┐
│ PROCHAINE ACTION                                             │
│ Prochain rendez-vous · 24 août 2026 10:30                  │
│ Source : Agenda · date réelle                    [Ouvrir →]  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ PLAN ACTIF       │ │ PROCHAIN RDV     │ │ FINANCES         │
│ 2 étapes en cours│ │ 24 août · 10:30  │ │ 1 200 MAD        │
│ Source: Master   │ │ Source: Agenda   │ │ Actes + paiements│
│ Plan · date      │ │ · date           │ │ · date activité  │
└──────────────────┘ └──────────────────┘ └──────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ CHRONOLOGIE FACTUELLE                                        │
│ [événement] [date] [Source : …]                 [Ouvrir →]  │
│ [événement] [date] [Source : …]                 [Ouvrir →]  │
└──────────────────────────────────────────────────────────────┘
```

États neutres obligatoires :
- aucun RDV futur => « Aucun RDV planifié » ;
- aucun Master Plan => « Aucun plan enregistré » ;
- `has_billing_data=false` => « Solde indéterminé » ;
- aucune prochaine action factuelle => « Aucune action planifiée ».

## Succès observable
1. `FlashSummary` n’est plus rendu dans la Vue d’ensemble.
2. Une carte « Prochaine action » existe et ne repose que sur Appointment ou une étape PENDING enregistrée.
3. Plan actif, prochain RDV et finances affichent une provenance explicite et un état neutre honnête.
4. Treatment Plan ouvre l’espace Clinique / Master Plan, jamais Documents.
5. Chaque événement navigable expose une action « Ouvrir la source ».
6. Zéro overflow horizontal global, zéro runtime error, zéro HTTP 5xx sur 390/430/768/1280.
7. Aucun changement du contrat clinique P0 : pas de diagnostic/risk score/traitement automatique ajouté.

## Preuve requise
- Tests backend ciblés Journey vérité/provenance.
- Tests frontend ciblés + build.
- Workflow AFTER dédié mêmes 4 viewports.
- Comparaison baseline / wireframe / AFTER.
- CI + T2 exact-HEAD.
- Certificat P2 et roadmap uniquement après preuves.
