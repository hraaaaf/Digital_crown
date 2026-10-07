# Digital Crown — Canonical Adaptive First User Experience Audit Prompt

## Goal
Évaluer la première expérience réelle d'un utilisateur sur un périmètre donné de Digital Crown, jusqu'à une première valeur métier observable, sans appliquer automatiquement un référentiel d'onboarding SaaS minimaliste.

Le référentiel FUE doit d'abord comprendre ce que l'utilisateur est réellement en train de faire, puis adapter :
- la définition de First Value ;
- les étapes attendues ;
- la tolérance au nombre d'étapes ;
- les critères de charge cognitive ;
- les poids de scoring ;
- les risques et plafonds applicables.

Le nombre d'étapes n'est jamais un défaut en soi. Une étape est pénalisée uniquement si elle est inutile, mal séquencée, ambiguë, non récupérable, disproportionnée ou bloque la valeur attendue.

## 1. Mandatory Context Classification

Avant tout score, classifier explicitement le scénario FUE.

### FUE-A — Installation initiale cabinet / clinique
Exemples : première configuration du cabinet, identité légale et professionnelle, spécialités, coordonnées, paramètres documentaires, branding, QR/canaux, préférences institutionnelles, rôles ou topologie de poste.

Doctrine :
- un parcours long peut être normal ;
- les décisions de configuration durable sont légitimes avant la première utilisation ;
- ne pas pénaliser la profondeur si chaque étape correspond à une vraie décision d'installation ;
- évaluer surtout clarté, défauts raisonnables, possibilité de revenir, reprise, preview, sauvegarde, cohérence et transition vers l'exploitation.

### FUE-B — Première utilisation d'un utilisateur dans un cabinet déjà configuré
Exemples : dentiste, secrétaire, assistant, remplaçant, utilisateur mobile.

Doctrine :
- configuration institutionnelle déjà faite ;
- l'utilisateur doit atteindre rapidement son espace utile ;
- toute demande de configuration cabinet redondante est fortement pénalisée ;
- privilégier rôle, permissions, orientation et première tâche.

### FUE-C — Activation / découverte d'un module
Exemples : Documents, Comptabilité, Agenda, Imagerie, IAmina, Mobile, Céphalométrie.

Doctrine :
- ne pas rejouer l'onboarding global ;
- First Value = premier résultat utile propre au module ;
- préférer l'apprentissage contextuel et progressif à une longue configuration préalable non nécessaire.

### FUE-D — Première exécution d'un workflow métier
Exemples : créer un patient, créer un rendez-vous, générer un devis, saisir un paiement, importer une radio, produire un certificat.

Doctrine :
- mesurer le chemin de l'intention à l'ACK métier observable ;
- chaque étape doit être nécessaire au contrat métier, à la safety ou à l'intégrité ;
- les contrôles anti-erreur sont légitimes s'ils sont proportionnés et compréhensibles.

### FUE-E — Première utilisation d'un workflow clinique / safety-critical
Exemples : prescription, diagnostic assisté, panoramique, céphalométrie, interprétation clinique.

Doctrine :
- la vitesse n'est jamais prioritaire sur la safety ;
- confirmations, provenance, incertitude, validation praticien et données requises peuvent justifier des étapes supplémentaires ;
- ne jamais pénaliser une friction nécessaire à une barrière de sécurité correctement conçue.

### FUE-F — Reprise / migration / nouvel environnement
Exemples : nouveau poste, restauration, migration de version, reprise après installation, changement de workstation role.

Doctrine :
- First Value = retour sûr à l'état opérationnel attendu ;
- priorité à continuité, détection de contexte, récupération, absence de perte de données et transparence de l'état.

### FUE-G — Autre scénario
Si aucun type ne correspond, définir explicitement : rôle utilisateur, état initial, objectif métier, First Value, risques dominants et contraintes justifiant éventuellement un parcours long.

Interdiction : ne jamais scorer avant d'avoir effectué cette classification.

## 2. Define the User and Initial State

Avant navigation, documenter :
- rôle réel ou simulé ;
- niveau d'expertise supposé ;
- cabinet vierge ou configuré ;
- données déjà disponibles ;
- permissions ;
- device / viewport ;
- état de session ;
- objectif utilisateur ;
- dépendances externes pertinentes.

Ne pas supposer qu'un utilisateur first use est nécessairement novice du métier. Il peut être expert dentaire mais nouveau dans Digital Crown.

## 3. Define First Value Before Execution

La First Value doit être définie avant le test.

Elle doit être :
- observable ;
- utile dans le contexte réel ;
- obtenue par le chemin produit normal ;
- suffisamment forte pour que l'utilisateur puisse dire : « j'ai accompli quelque chose d'utile ».

Exemples :
- FUE-A installation cabinet : configuration enregistrée + environnement opérationnel cohérent ;
- FUE-B utilisateur : accès à son espace et première tâche réalisable ;
- FUE-C module : premier résultat utile du module ;
- FUE-D workflow : écriture/ACK métier réussi et visible ;
- FUE-E clinique : résultat ou signal correctement produit avec garde-fous et validation requise ;
- FUE-F reprise : état opérationnel récupéré sans ambiguïté.

Le Dashboard seul n'est First Value que si le scénario évalué définit explicitement cette arrivée comme résultat utile.

## 4. Necessity Test for Every Step

Pour chaque étape rencontrée, poser ces questions :
1. Cette étape est-elle nécessaire au scénario ?
2. Est-elle nécessaire maintenant, ou pourrait-elle être différée ?
3. Est-elle obligatoire pour une raison métier, légale, safety ou intégrité ?
4. Si facultative, est-elle clairement présentée comme facultative ?
5. Les valeurs par défaut sont-elles raisonnables ?
6. L'utilisateur peut-il revenir en arrière sans perdre son travail ?
7. Peut-il reprendre après interruption ?
8. L'interface explique-t-elle pourquoi cette décision est demandée ?
9. L'étape apporte-t-elle une preview ou un feedback proportionné à son importance ?
10. Le coût cognitif est-il cohérent avec la permanence de la décision ?

Règle : ne jamais pénaliser une étape légitime uniquement parce qu'elle augmente le Time-to-Value.

## 5. Environment and Evidence

Par défaut :
- runtime isolé, backend et frontend réels ;
- aucune donnée cabinet réelle ;
- pas de mocks sur le chemin nominal de succès sauf nécessité documentée ;
- mobile 390x844 + desktop 1280x900 quand le flow est responsive ;
- capture PNG aux checkpoints déterminants.

Pour chaque checkpoint :
- screenshot BEFORE ;
- screenshot AFTER si changement d'état ;
- URL/path ;
- viewport ;
- temps relatif ;
- interactions cumulées ;
- erreurs console/page ;
- HTTP 5xx ;
- overflow horizontal ;
- état de chargement / attente ;
- preuve de l'ACK métier attendu.

Pour les parcours très longs, les captures peuvent être regroupées par décision significative plutôt que par clic.

## 6. Checks Per Step

Noter sévèrement /10, en adaptant le poids au type de FUE :
- Compréhension immédiate.
- Hiérarchie visuelle.
- Pertinence de l'étape dans ce contexte.
- Charge cognitive proportionnée à l'importance de la décision.
- Feedback / état système.
- Navigation / retour / reprise.
- Défauts et préremplissages.
- Facultatif vs obligatoire.
- Mobile.
- Desktop.
- Accessibilité observable.
- Truthfulness / absence de faux succès.
- Safety / intégrité.
- Performance perçue.
- Continuité vers l'étape suivante.
- Qualité du First Value.

Important : une configuration institutionnelle durable peut légitimement demander plus d'effort qu'une action quotidienne. Une barrière clinique ou financière peut légitimement demander confirmation. Une décision irréversible doit recevoir plus d'explication qu'un choix cosmétique.

## 7. Scenario-Adaptive Scoring

### FUE-A — Installation cabinet / clinique
- entrée/auth/contexte : 10%
- configuration institutionnelle : 45%
- qualité des défauts / previews / reprise : 15%
- finalisation / transition opérationnelle : 20%
- première capacité métier démontrable : 10%

Ne pas appliquer de pénalité automatique au nombre d'étapes.

### FUE-B — Nouvel utilisateur
- entrée/auth : 15%
- orientation rôle/permissions : 20%
- découverte de la tâche principale : 25%
- exécution première tâche : 30%
- feedback / continuité : 10%

### FUE-C — Nouveau module
- découvrabilité : 20%
- compréhension : 20%
- configuration nécessaire : 15%
- première action : 25%
- résultat / continuité : 20%

### FUE-D — Workflow métier
- entrée dans le workflow : 10%
- saisie / contrôles nécessaires : 25%
- prévention d'erreur / truthfulness : 20%
- ACK / résultat : 30%
- continuité : 15%

### FUE-E — Workflow clinique / safety-critical
- contexte / données requises : 20%
- garde-fous / provenance / incertitude : 30%
- compréhension praticien : 20%
- résultat + validation humaine : 20%
- continuité / traçabilité : 10%

### FUE-F — Reprise / migration
- détection de contexte : 20%
- sécurité / intégrité des données : 30%
- récupération : 25%
- transparence de l'état : 15%
- retour opérationnel : 10%

### FUE-G
Définir les poids avant exécution et les justifier.

## 8. Severity

- P0 : blocage critique, perte/corruption de données, sécurité/safety critique, action dangereuse.
- P1 : empêche ou compromet fortement First Value, impasse, faux succès, transition instable majeure, décision importante incompréhensible.
- P2 : friction réelle mais contournable, défaut de hiérarchie, wording, densité, défauts perfectibles, polish.

Score ceilings :
- P0 ouvert => global <= 4.0
- P1 empêchant First Value => global <= 6.0
- impasse mobile sur flow mobile obligatoire => mobile <= 5.0
- faux succès => étape concernée <= 3.0
- First Value non observable => FUE non validé, global <= 5.0

Un P1 qui n'empêche pas la First Value peut réduire fortement le score sans déclencher automatiquement le plafond <= 6.0 ; justifier le traitement.

## 9. Time-to-Value Interpretation

Toujours mesurer le temps, mais ne jamais utiliser le temps seul comme proxy de qualité.

Interprétation :
- configuration durable : un temps plus long peut être acceptable ;
- tâche quotidienne : temps et nombre d'interactions deviennent plus importants ;
- workflow safety-critical : le temps est secondaire si la friction protège un invariant réel ;
- reprise/migration : la prévisibilité et l'absence de perte comptent plus que la vitesse brute.

Rapporter : temps total, temps actif estimé, temps d'attente système, nombre d'interactions et nombre de décisions significatives.

## 10. Adversarial Reviews

### Perspective 1 — Adoption / UX / Accessibilité
Chercher : confusion, étapes mal séquencées, charge cognitive disproportionnée, mauvaise découvrabilité, défauts inadéquats, fatigue/densité, pièges mobile/desktop, manque de reprise, incohérence entre importance d'une décision et effort demandé.

### Perspective 2 — Truthfulness / Safety / System State
Chercher : faux succès, état intermédiaire ambigu, mutation avant ACK, fail-open, données inventées, erreur silencieuse, loading sans vérité d'état, incohérence frontend/backend, transition post-ACK instable, preuve insuffisante.

Après corrections significatives, revoir uniquement le scope impacté + dépendances directes selon la doctrine projet.

## 11. Output

Toujours produire :
1. FUE type + justification.
2. Persona / état initial / First Value.
3. Tableau des étapes réellement observées avec score /10, temps cumulé, interactions, finding principal et statut nécessaire / facultatif / différable.
4. Findings P0/P1/P2 avec preuve.
5. Temps : setup ou préparation, attente système, First Value.
6. Score mobile.
7. Score desktop.
8. Score global.
9. Deux revues adversariales.
10. Passe de confirmation.
11. Top 5 corrections par impact sur réussite du scénario, pas automatiquement par réduction du nombre d'étapes.
12. Ce qui ne doit pas être simplifié parce que la complexité est légitime.
13. Next exact.

## 12. Digital Crown FUE Lab

Référence canonique : FUE — PR #783.

Pour un lot futur :
- FUE: PR #783
- préciser le type FUE (A–G) ;
- préciser le scénario ;
- définir First Value avant exécution ;
- ajouter ou réutiliser le harness correspondant.

Les corrections produit restent dans leurs PR/lots respectifs. PR #783 sert de laboratoire de tests, prompts, scénarios, métriques et preuves FUE.