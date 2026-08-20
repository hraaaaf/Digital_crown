# Patient P4 — Imagerie

## Goal
Réunir RVG, Panoramique et Céphalométrie dans un seul espace Imagerie cohérent, en conservant les contrats scientifiques propres à chaque modalité et en supprimant les comportements qui inventent, surinterprètent ou détruisent irréversiblement une donnée clinique.

## Succès observable
1. Trois entrées explicites dans Imagerie : `RVG`, `Panoramique`, `Céphalométrie`.
2. RVG réutilise le cycle déjà certifié P0-F : upload/listing, blob authentifié, isolation tenant, corbeille/restauration. Aucun nouveau stockage parallèle.
3. Panoramique conserve la détection automatique limitée aux repères/dents et distingue explicitement ce qui est saisi/validé par le praticien.
4. Céphalométrie n’invente jamais âge/sexe en cas d’échec de lecture Patient.
5. Céphalométrie n’auto-remplit pas une stratégie thérapeutique dans le dossier à partir d’un calcul interne.
6. Les permissions frontend correspondent aux permissions backend propres à chaque modalité ; une fonction non autorisée n’est pas présentée comme disponible.
7. Panoramique et Céphalo ont un cycle historique/suppression/restauration cohérent et traçable. Pas de hard-delete depuis l’UI normale.
8. Aucun libellé `IA`, `détection IA`, `diagnostic intelligent` si la fonction réelle est déterministe, limitée à des repères, ou si la provenance n’est pas explicitée.
9. Aucun changement des formules/normes scientifiques sans certification dédiée.
10. Zéro overflow horizontal, erreur runtime ou HTTP 5xx sur 390x844, 430x932, 768x1024 et 1280x900.

## Baseline / audit initial

### Navigation Patient
`PatientDetailsInner.tsx` exposait seulement `Céphalométrie` et `Panoramique`. `RVG` existait déjà dans le repo mais n’était pas intégré à cette navigation.

### RVG
Contrat certifié existant P0-F (`docs/PATIENT_P0F_RVG_CERT.json`) : authentification par header, isolation tenant, corbeille/restauration récupérable, rendu via blob authentifié, build frontend.

### Panoramique
Le backend `upload-panoramic` limite la vision automatique au repérage dentaire. L’UI exposait encore des termes legacy `IA/SOTA/Intelligence Clinique` et le DELETE normal effaçait ligne DB + fichier.

### Céphalométrie
`CephaloWorkspace.tsx` contenait fallback `age: 20`, `sexe: M` et auto-remplissage de `strategie_therapeutique` via `generateTreatmentPlan()`.

## Wireframe cible

```text
IMAGERIE
[ RVG ] [ PANORAMIQUE ] [ CÉPHALOMÉTRIE ]

RVG
┌─────────────────────────────────────────────────────────────┐
│ Radios intra-orales                           [Ajouter RVG]  │
│ [carte RVG] [carte RVG] ...                                  │
│ Ouvrir · Télécharger · Corbeille                             │
└─────────────────────────────────────────────────────────────┘

PANORAMIQUE
┌─────────────────────────────────────────────────────────────┐
│ Image / repères dentaires                                   │
│ Constatations du praticien                                  │
│ Rapport déterministe + édition praticien                    │
│ [Historique] [Corbeille]                                    │
└─────────────────────────────────────────────────────────────┘

CÉPHALOMÉTRIE
┌─────────────────────────────────────────────────────────────┐
│ Image · calibration · landmarks · mesures                   │
│ Données Patient requises, jamais de fallback inventé        │
│ Interprétation / stratégie uniquement si validée            │
│ [Historique] [Corbeille]                                    │
└─────────────────────────────────────────────────────────────┘
```

## Implémentation actuelle — non certifiée tant que les gates ne sont pas exécutés

### P4-A — Vérité / sécurité
- sous-navigation `RVG → Panoramique → Céphalométrie`.
- RBAC modalité miroir backend ; URL non autorisée normalisée vers une modalité accessible.
- Céphalo : aucune donnée `20/M` inventée ; données Patient absentes/invalides => blocage explicite `Données Patient requises`.
- Céphalo : aucun auto `generateTreatmentPlan()`.
- Panoramique : UI `Repérage dentaire automatique · validation praticien`, `Moteur déterministe`, `Constatations`; labels IA/SOTA/Zéro-Hallucination retirés.

### P4-B — RVG
- `PatientRvgPanel` réutilise `rvgService`, `RvgCard`, `RvgUploadModal`; aucun nouveau stockage.

### P4-C — Lifecycle récupérable
- migration additive `f7a8b9c0d1e2` après P3 `e6f7a8b9c0d1`.
- `imaging_trash_records` séparé des tables scientifiques.
- DELETE normal = marqueur de corbeille ; analyse + fichier conservés.
- Historique/Corbeille/Restaurer pour Pano et Céphalo ; listes actives soustraient les IDs trashés.
- Journey P2 conservé comme agrégateur, façade P4 retire seulement les événements imagerie trashés.
- CMO déterministe/non prescriptif ignore la corbeille et dérive le cabinet depuis `Patient.employer_id`.

## Preuves préparées
- backend lifecycle : non-destruction ligne/fichier, restore, tenant, RBAC.
- UI contract : navigation/RBAC, vérité Céphalo, terminologie Pano, corbeille/restauration.
- AFTER : RVG/Pano/Céphalo × 390/430/768/1280 = 12 captures.

## Reste avant CLOSED
1. resynchroniser P4 sur P3 final ;
2. CI + T2 + backend + UI-contract + AFTER exact-HEAD ;
3. inspecter les 12 captures et scorer ;
4. certificat + roadmap ;
5. recertification closeout exact-HEAD.

## Règles
- ne pas refaire le RVG déjà certifié ;
- pas de donnée clinique inventée ;
- pas de stratégie thérapeutique automatique ;
- pas de hard-delete comme action normale ;
- aucune modification scientifique silencieuse ;
- aucun déploiement Vercel.
