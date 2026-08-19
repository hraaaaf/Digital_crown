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
`PatientDetailsInner.tsx` expose actuellement seulement deux sous-onglets Imagerie : `Céphalométrie` et `Panoramique`. `RVG` existe dans le repo mais n’est pas intégré à cette navigation.

### RVG
Contrat certifié existant P0-F (`docs/PATIENT_P0F_RVG_CERT.json`) :
- authentification par header ;
- isolation tenant ;
- corbeille/restauration récupérable ;
- rendu via blob authentifié ;
- frontend build.

Composants/services existants à conserver :
- `frontend/src/services/rvgService.ts` ;
- `frontend/src/features/patients/components/RvgCard.tsx` ;
- `frontend/src/features/patients/components/RvgUploadModal.tsx` ;
- endpoints Documents `/documents/patients/{patient_id}/rvg` et cycle `/trash` / `/restore`.

### Panoramique
Le backend `upload-panoramic` indique explicitement que la vision automatique nomme les dents uniquement et que la sémiologie est saisie manuellement. En revanche, l’UI et certaines docstrings conservent encore des termes legacy comme `diagnostics`, `anomalies détectées`, `détections IA`.

L’historique panoramique appelle actuellement `DELETE /ia/panoramic/{id}`. Le backend supprime la ligne DB et le fichier physique. Ce cycle n’est pas récupérable.

### Céphalométrie
`CephaloWorkspace.tsx` contient deux comportements incompatibles avec la doctrine de vérité :
- échec de lecture Patient => fallback `age: 20`, `sexe: M` ;
- auto-remplissage de `strategie_therapeutique` via `generateTreatmentPlan()` lorsqu’elle est vide.

Le commentaire de tête expose encore `SLM Integration` et `/patients/{id}/ai-diagnostic`, alors que P0 a supprimé le positionnement LLM comme vérité clinique.

L’historique céphalo appelle actuellement `DELETE /ia/cephalo/{id}`. Le backend supprime la ligne DB et le fichier physique.

### Permissions
Backend actuel :
- Céphalo : permission `cephalo` ;
- Panoramique : permission `panoramic` ;
- RVG : cycle Documents déjà durci, à recartographier précisément avant branchement UI.

Le sous-espace Imagerie lui-même n’applique pas encore une matrice frontend par modalité.

## Découpage P4

### P4-A — Vérité / sécurité Imagerie
- supprimer les fallbacks démographiques céphalo ;
- supprimer l’auto-remplissage thérapeutique ;
- neutraliser les libellés legacy `IA`/`diagnostic intelligent` qui ne correspondent plus au contrat réel ;
- vérifier les tâches de synthèse en arrière-plan avant conservation.

### P4-B — RVG intégré
- ajouter RVG à la sous-navigation Imagerie ;
- réutiliser `rvgService`, `RvgCard`, `RvgUploadModal` ;
- aucun changement au contrat P0-F sans nouvelle preuve ;
- états chargement/erreur/vide explicites.

### P4-C — Historique récupérable
- remplacer le hard-delete normal Panoramique/Céphalo par une corbeille traçable ;
- restaurer depuis l’historique/corbeille ;
- ne supprimer physiquement qu’au travers d’une action permanente séparée et explicitement autorisée si cette fonction est réellement nécessaire.

### P4-D — Permissions + certification
- matrice frontend/backend RVG/Pano/Céphalo ;
- tests isolation Patient A→B/tenant ;
- certifications scientifiques Panoramique et Céphalo séparées ;
- AFTER mêmes viewports/modes que BEFORE ;
- CI + T2 exact-HEAD.

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

## Preuve requise
- BEFORE P4 sur 390/430/768/1280 pour l’espace Céphalo et Panoramique actuels ;
- source contract RVG P0-F ;
- tests permissions et lifecycle par modalité ;
- tests scientifiques ciblés sans élargir les règles cliniques ;
- AFTER mêmes viewports/modes ;
- comparaison BEFORE / wireframe / AFTER ;
- CI + T2 exact-HEAD ;
- certificat P4 puis roadmap.

## Règles
- ne pas refaire le RVG déjà certifié ;
- pas de donnée clinique inventée pour permettre au calcul de continuer ;
- pas de stratégie thérapeutique automatique ;
- pas de hard-delete comme action normale d’une imagerie clinique ;
- aucune modification scientifique silencieuse ;
- aucun déploiement Vercel.
