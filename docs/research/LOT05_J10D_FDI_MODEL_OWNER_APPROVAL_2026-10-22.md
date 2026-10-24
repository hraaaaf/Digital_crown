# Digital Crown — LOT05 / 05.7-J10D — Décision propriétaire : modèle FDI retenu

**Date : 22 octobre 2026.** **Autorité : validation explicite du propriétaire du produit dans la conversation (« Je valide le modele »).**

## Décision : VALIDÉ POUR LA SÉLECTION PRODUIT ET LE PROTOTYPAGE, PAS POUR LE DÉPLOIEMENT CLINIQUE

Le propriétaire de Digital Crown **retient définitivement comme modèle candidat de localisation et numérotation des dents permanentes** :

- **Modèle** : [miquic/app-odonto-fdi-yolov8s](https://huggingface.co/miquic/app-odonto-fdi-yolov8s) — YOLOv8s, 32 classes FDI 11–48, sans pathologie ni propositions d'actes.
- **Version épinglée** : Hugging Face `82b4d9a02f9e6f32a746dc17afe681e20e8b99e2`.
- **Poids** : `best.pt`, SHA256 `533833a4244f092f82bc94a6c2d6fac7e1656c9437994e98d09843c54aafd3f6`.
- **Preuve technique et métrique externe initiale** : [GitHub Actions #39764642070](https://github.com/hraaaaf/Digital_crown/actions/runs/39764642070), code testé `4af6e5e67e94d35dd918d2f134a5ac16cb6ef855`, sur 40 panoramiques publiques AKUDENTAL (1 036 dents référencées). Rappel de localisation 86,583 % ; rappel dents correctement localisées **et** numérotées 81,081 % ; 50 confusions FDI voisines ; 139 dents non localisées ; 3 panoramiques complètement correctes sur 40. Le compte rendu complet est `docs/research/LOT05_J10D_AKUDENTAL_FDI_REAL40_RESULTS.md`.

Cette validation signifie : **le choix entre modèles concurrents est clos**, le modèle devient **référence technique pour la prochaine phase expérimentale** (compatibilité Windows/ONNX, calibrage, ergonomie de localisation FDI corrigeable par le praticien). Il n'est plus nécessaire de relancer une recherche généraliste d'autres modèles simplement pour décider quoi prototyper ; les tests de robustesse et comparateurs demeurent possibles si une défaillance le justifie.

## Comportement du futur parcours — engagements produit

1. En ouvrant une panoramique locale, Digital Crown propose une région par dent visible et un numéro FDI pour les **dents permanentes uniquement** ; aucun comptage forcé à 32.
2. Le praticien doit pouvoir **déplacer, redimensionner, ajouter, supprimer et renuméroter** une proposition, gérer explicitement une dent absente / un doublon, et **confirmer** avant qu'un acte ne soit associé à cette dent dans le dossier.
3. Le clic sur une **dent confirmée** ouvre un catalogue d'actes **par spécialité** ; le praticien sélectionne les actes **manuellement**, et peut créer des définitions d'actes supplémentaires dans un dictionnaire local persistant, selon des spécifications et lots ultérieurs autorisés.
4. Le modèle n'effectue **aucun diagnostic**, ne reconnaît pas les pathologies, ne prescrit pas et ne propose ni ne choisit d'actes. La denture temporaire/mixte et les implants nécessitent un traitement spécifique ou une saisie manuelle — pas de FDI temporaire inférée par ce modèle adulte.
5. Les radiographies et annotations du cabinet ne doivent jamais être envoyées vers GitHub/HF ou un service tiers. Traitement patient local, permissions et audit à respecter.

## Risques explicitement maintenus — ne pas confondre acceptation et certification

- **Clinical GO : NON.** La précision sur 40 images est insuffisante pour un système autonome ; les numéros proposés sont *non confirmés* avant revue du dentiste. Aucune validation réglementaire, multisite ou sécurité patient indépendante.
- **Commercial licence GO : NON.** Les poids du modèle et leur dataset d'entraînement affichent **CC BY-NC-SA 4.0 (noncommercial)**. L'approbation du propriétaire **ne constitue pas une licence commerciale** et ne permet pas de bundler/distribuer le `.pt`/ONNX dans un logiciel commercial sans droits séparés.
- **Windows/ONNX GO : NON, à prouver.** Aucune parité avec `.pt`, packaging, exploitation sûre ou performance sur machine cliente validés.
- **Clinical holdout independence : NON.** Pas de preuve d'absence de doublons patients/images entre AKUDENTAL et les données d'entraînement ; les labels GT nécessitent revue sur certains films.
- **Production merge / installer / Vercel / patient DB : NON.** Aucune autorisation explicite d'intégration ou publication clinique n'a été donnée par « Je valide le modele ». Les PR d'expérimentation demeurent DRAFT/non fusionnées. V1.5 reste **NO-GO**.

## Prochaine étape recommandée (sans la déclarer déjà effectuée)

Concevoir et tester **un contrat local Windows ONNX avec parité déterministe sur échantillons autorisés et une maquette d'interface de numérotation FDI entièrement modifiable**, avec validations et lots distincts, sans apporter d'éléments de diagnostics. Préparer un plan d'obtention de droits commerciaux et de revue clinique indépendante avant toute distribution.

**Décision de gouvernance :** modèle FDI **CHOISI / VALIDÉ PAR LE PROPRIÉTAIRE** ; **développement expérimental possible sous gouvernance**, mais **certification clinique et distribution restent bloquées**.
