# Patient P0-D — Remaining Assistants Fail-Closed Visual Goal

## Lot

Assistants concernés : Général, Parodontologie, Prothèse & Esthétique, Orthodontie (ODF), Occlusodontie & ATM.

## Baseline à capturer avant modification produit

Écran réel : fiche Patient → Examen Clinique → carte de l'assistant → questionnaire existant → résultat actuel.

Viewports obligatoires : 390×844, 430×932, 768×1024, 1280×900.

La structure actuelle doit rester la référence : cartes, QCM, typographie, boutons, couleurs et emplacement du résultat ne sont pas redesignés dans ce lot.

## Goal

Conserver exactement l'expérience de collecte existante, mais empêcher qu'un QCM court transforme automatiquement les réponses en diagnostic retenu, prescription, imagerie, dispositif, orientation ou plan thérapeutique.

Le résultat final devient uniquement une synthèse descriptive des réponses saisies, explicitement soumise à validation du praticien.

## Succès observable

1. mêmes cartes et mêmes questions avant/après ;
2. aucune prescription, antibioprophylaxie, CBCT/IRM, gouttière, appareillage, traitement ou ordre inter-spécialités ajouté automatiquement ;
3. aucune étape n'est ajoutée automatiquement au Master Plan ;
4. le résultat final décrit les réponses renseignées et indique que diagnostic/examens/conduite relèvent du praticien ;
5. aucun changement volontaire de layout, couleur, taille ou navigation ;
6. zéro overflow document, zéro erreur runtime et zéro HTTP 5xx sur les 4 viewports ;
7. comparaison avant / référence / après obligatoire avant certification.

## Référence visuelle / wireframe

Avant, structure actuelle :

```text
┌─────────────────────────────────────────────┐
│ Protocole [spécialité]                     │
│                                             │
│ Question N / M                              │
│ [option A]                                  │
│ [option B]                                  │
│ [option C]                                  │
└─────────────────────────────────────────────┘
                 ↓ dernière réponse
┌─────────────────────────────────────────────┐
│ Résultat actuel                             │
│ diagnostic / actions calculés               │
└─────────────────────────────────────────────┘
```

Cible, même surface :

```text
┌─────────────────────────────────────────────┐
│ Protocole [spécialité]                     │
│                                             │
│ Question N / M                              │
│ [option A]                                  │
│ [option B]                                  │
│ [option C]                                  │
└─────────────────────────────────────────────┘
                 ↓ dernière réponse
┌─────────────────────────────────────────────┐
│ Synthèse structurée                         │
│ Observations recueillies : …                │
│ Aucun diagnostic/traitement automatique.    │
│ Décision et validation : praticien.         │
└─────────────────────────────────────────────┘
```

## Hors scope

- redesign des assistants ;
- ajout de nouvelles règles diagnostiques ou thérapeutiques ;
- modification du Master Plan ;
- nouveau moteur clinique ;
- changement de navigation ClinicalHub.
