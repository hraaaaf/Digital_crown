# Patient P0-D — Matrice des règles cliniques automatisées

## Goal

Prouver, assistant par assistant, qu'aucune sortie de questionnaire ne devient automatiquement diagnostic retenu, prescription, imagerie, dispositif, orientation ou traitement.

## Règle de certification

Une source scientifique primaire est obligatoire pour toute règle thérapeutique automatisée conservée. Si aucune règle thérapeutique automatisée n'est conservée, la colonne source est `N/A — aucune règle thérapeutique automatisée` et la preuve attendue est un contrat fail-closed + `steps=[]` + validation praticien explicite.

| Assistant | Fonction active | Règle thérapeutique automatique conservée | Source primaire requise | Validation praticien | État |
|---|---|---:|---|---|---|
| Examen clinique complet | Collecte / synthèse descriptive | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | CERTIFIÉ antérieurement |
| Endodontie | Collecte douleur / sensibilité / observation radio | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | CERTIFIÉ source actuelle |
| Chirurgie orale | Collecte pré-opératoire / vigilance | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | CERTIFIÉ source actuelle |
| Pédodontie | Collecte denture / motif / coopération | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | CERTIFIÉ source actuelle |
| Médecine buccale / Pathologie | Collecte aspect / durée / symptômes / vigilance | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | CERTIFIÉ source actuelle |
| ATM / Occlusodontie | Collecte symptômes / parafonctions / contexte | **À supprimer du code legacy** | N/A après neutralisation | Obligatoire | PENDING closeout atomique |
| Orthodontie | Collecte structurée | **À supprimer du code legacy** | N/A après neutralisation | Obligatoire | PENDING closeout atomique |
| Parodontologie | Collecte structurée | **À supprimer du code legacy** | N/A après neutralisation | Obligatoire | PENDING closeout atomique |
| Prothèse & Esthétique | Collecte structurée | **À supprimer du code legacy** | N/A après neutralisation | Obligatoire | PENDING closeout atomique |
| AssistantGeneral.tsx | Code non utilisé par le routage `general` actuel ; neutralisé par défense en profondeur | **À supprimer du code legacy** | N/A après neutralisation | Obligatoire | PENDING closeout atomique |

## Contrat fail-closed cible commun

- sortie descriptive des réponses réellement saisies ;
- aucune conclusion diagnostique automatique ;
- aucune prescription, antibiothérapie, sédation, anesthésie ou médicament automatique ;
- aucune imagerie automatiquement prescrite ;
- aucun dispositif, acte, orientation ou traitement automatique ;
- `onComplete(summary, [])` ou contrat équivalent sans étape thérapeutique ;
- décision finale explicitement réservée au praticien.

## Preuves déjà acquises

- `AssistantEndo.tsx` : observations, données à confirmer, aucun diagnostic pulpaire/péri-apical automatique, `onComplete(summary, [])`.
- `AssistantChirurgie.tsx` : aucun diagnostic chirurgical, examen complémentaire, protocole médicamenteux ou geste opératoire automatique, `onComplete(summary, [])`.
- `AssistantPedo.tsx` : aucun diagnostic, examen radiographique, sédation, anesthésie, prescription ou traitement automatique, `onComplete(summary, [])`.
- `AssistantPatho.tsx` : aucun diagnostic, médicament, biopsie, exérèse, surveillance ou adressage automatique, `onComplete(summary, [])`.
- `ClinicalHub.tsx` : une proposition d'assistant reste session-only et ne mute pas le Master Plan autoritatif.

## Gate de fermeture

Cette matrice ne passe à `CERTIFIED` globalement qu'après :
1. neutralisation ATM / Ortho / Paro / Prothèse / AssistantGeneral ;
2. build frontend ;
3. captures AFTER 390 / 430 / 768 / 1280 ;
4. preuve que les sorties finales contiennent le contrat fail-closed ;
5. CI exacte sur le HEAD produit final.
