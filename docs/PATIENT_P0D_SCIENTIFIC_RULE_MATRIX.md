# Patient P0-D — Matrice des règles cliniques automatisées

## Goal

Prouver, assistant par assistant, qu'aucune sortie de questionnaire ne devient automatiquement diagnostic retenu, prescription, imagerie, dispositif, orientation ou traitement.

## Règle de certification

Une source scientifique primaire est obligatoire pour toute règle thérapeutique automatisée conservée. Si aucune règle thérapeutique automatisée n'est conservée, la colonne source est `N/A — aucune règle thérapeutique automatisée` et la preuve attendue est un contrat fail-closed + `steps=[]` + validation praticien explicite.

| Assistant | Fonction active | Règle thérapeutique automatique conservée | Source primaire requise | Validation praticien | État |
|---|---|---:|---|---|---|
| Examen clinique complet | Collecte / synthèse descriptive | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source actuelle |
| Endodontie | Collecte douleur / sensibilité / observation radio | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source actuelle |
| Chirurgie orale | Collecte pré-opératoire / vigilance | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source actuelle |
| Pédodontie | Collecte denture / motif / coopération | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source actuelle |
| Médecine buccale / Pathologie | Collecte aspect / durée / symptômes / vigilance | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source actuelle |
| ATM / Occlusodontie | Collecte symptômes / parafonctions / contexte | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source + AFTER |
| Orthodontie | Collecte structurée | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source + AFTER |
| Parodontologie | Collecte structurée | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source + AFTER |
| Prothèse & Esthétique | Collecte structurée | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source + AFTER |
| AssistantGeneral.tsx | Code non utilisé par le routage `general` actuel ; neutralisé par défense en profondeur | Non | N/A — aucune règle thérapeutique automatisée | Obligatoire | VÉRIFIÉ source actuelle |

## Contrat fail-closed commun

- sortie descriptive des réponses réellement saisies ;
- aucune conclusion diagnostique automatique ;
- aucune prescription, antibiothérapie, sédation, anesthésie ou médicament automatique ;
- aucune imagerie automatiquement prescrite ;
- aucun dispositif, acte, orientation ou traitement automatique ;
- `onComplete(summary, [])` ou contrat équivalent sans étape thérapeutique ;
- décision finale explicitement réservée au praticien.

## Preuves acquises

- `AssistantEndo.tsx` : observations, données à confirmer, aucun diagnostic pulpaire/péri-apical automatique, `onComplete(summary, [])`.
- `AssistantChirurgie.tsx` : aucun diagnostic chirurgical, examen complémentaire, protocole médicamenteux ou geste opératoire automatique, `onComplete(summary, [])`.
- `AssistantPedo.tsx` : aucun diagnostic, examen radiographique, sédation, anesthésie, prescription ou traitement automatique, `onComplete(summary, [])`.
- `AssistantPatho.tsx` : aucun diagnostic, médicament, biopsie, exérèse, surveillance ou adressage automatique, `onComplete(summary, [])`.
- `AssistantExamenComplet.tsx` : synthèse d'observations et vigilance, `steps=[]`, diagnostic et conduite réservés au praticien.
- `AssistantATM.tsx`, `AssistantOrtho.tsx`, `AssistantParo.tsx`, `AssistantProthese.tsx`, `AssistantGeneral.tsx` : synthèse descriptive explicite, aucun diagnostic/examen/médicament/dispositif/orientation/traitement automatique, `onComplete(summary, [])`.
- `ClinicalHub.tsx` : une proposition d'assistant reste session-only et ne mute pas le Master Plan autoritatif.
- AFTER visuel P0-D : run `32150937781`, artifact `9329967519`, 20 captures 390/430/768/1280, proposition visible partout, zéro overflow document, zéro erreur runtime, zéro HTTP 5xx. Le run est rouge uniquement parce que le test cherchait le marqueur textuel des quatre assistants neutralisés dans le routage `general`, qui ouvre `AssistantExamenComplet` et utilise un garde-fou équivalent mais formulé différemment. Les captures ont été inspectées manuellement.

## Gate de fermeture

P0-D peut être déclaré certifié globalement uniquement après CI exacte sur le HEAD produit final et closeout documentaire du chantier P0. Le comportement source et la preuve visuelle AFTER sont acquis ; la CI finale du P0 reste le dernier gate transversal.
