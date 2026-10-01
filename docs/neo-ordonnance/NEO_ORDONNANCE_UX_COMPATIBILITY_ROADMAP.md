# Neo Ordonnance — UX Compatibility & Search Roadmap

Dernière mise à jour : 2026-10-01

## Principe produit verrouillé

Neo Ordonnance améliore la recherche, la provenance, les garde-fous et la sécurité **sans supprimer la logique de prescription praticien qui existait avant Neo**.

Le praticien reste l'auteur de chaque ligne. Le catalogue et les garde-fous documentent / vérifient ; ils ne remplacent pas la personnalisation explicite.

### Contrat de ligne obligatoire

Chaque ligne doit conserver :

- type de ligne explicite avec contrôle visuel :
  - 💊 **Médicament** ;
  - 🩻 **Radio / Examen** ;
- nom / DCI ou libellé d'examen ;
- présentation / identité catalogue quand une présentation exacte est choisie ;
- **forme** modifiable ;
- **dosage** modifiable ;
- **posologie** personnalisable ;
- **prise** ;
- **rythme / fréquence** ;
- **durée ou limite** ;
- **moment / condition** ;
- texte libre de posologie toujours disponible ;
- **non substituable (NS)** ;
- réordonnancement et suppression de ligne ;
- presets / habitudes praticien comme accélérateurs, jamais comme autorité clinique.

Le champ historique `quantite` reste dans le modèle et dans la persistance des préférences. Sa restitution UI / impression doit être réintroduite seulement après vérification du contrat document/PDF afin d'éviter une pseudo-fonction non imprimée.

## Ce que l'audit pré-Neo prouve

`PrescriptionAgenticStudioLegacy.tsx` gérait :
- suggestions médicaments, dosages et posologies ;
- recherche et détails issus des habitudes praticien ;
- formes via `FORMES` ;
- presets et protocoles ;
- saisie rapide ;
- détection de mots-clés radiologie/examen ;
- personnalisation de chaque ligne avant persistance.

Le modèle historique `DrugItem` conserve :
`name`, `dosage`, `forme`, `posologie`, `type`, `quantite`, `non_substituable` et l'identité catalogue.

## Ce que Neo possède déjà

`DrugRowV1.tsx` contient déjà :
- toggle 💊 via `Pill` / 🩻 via `Microscope` ;
- choix Forme ;
- choix Dose ;
- bouton NS ;
- Prescription Composer : Prise / Rythme / Durée ou limite / Moment ou condition ;
- phrase persistée ;
- textarea de posologie libre ;
- recherche catalogue `/medications/neo/search` ;
- safety patient read-only.

Le problème actuel n'est donc pas le composant de ligne principal : `PrescriptionAgenticStudioV1.tsx` a simplifié l'orchestration et passe actuellement des suggestions vides / handlers no-op, ce qui neutralise une partie de l'ergonomie pré-Neo.

## Roadmap révisée

### D5.1 — Catalogue national canonique
Statut : DONE sur branche D5.
- 9 931 identités nationales promues ;
- 0 suppression implicite ;
- idempotence stricte.

### D5.2 — Ranking médicament déterministe
Statut : IN PROGRESS.
- marque exacte > préfixe marque > préfixe token ;
- DCI exacte/préfixe ensuite ;
- substring/fuzzy en dernier ;
- popularité/habitudes seulement comme tie-breaker ;
- golden queries : DOL, DOLIPRANE, AMOX, IBUPROFENE.

### D5.3 — Compatibilité UX ligne pré-Neo
Goal : restaurer l'orchestration riche autour de `DrugRowV1` sans revenir aux suggestions cliniques automatiques.
- conserver 💊 Médicament / 🩻 Radio-Examen et leurs icônes ;
- conserver forme, dosage, NS ;
- conserver Prise / Rythme / Durée-limite / Moment-condition ;
- conserver texte libre ;
- restaurer suggestions praticien pour nom / dosage / posologie quand elles viennent des habitudes/presets ;
- une modification manuelle reste autorisée et explicite ;
- si une modification casse l'identité exacte catalogue, l'identité est invalidée/reliée proprement ; la saisie praticien n'est pas effacée arbitrairement ;
- vérifier le champ `quantite` jusqu'au PDF avant restauration UI.

### D5.4 — Recherche unifiée Médicaments + Protocoles
- même champ de recherche / expérience cohérente ;
- résultats typés `MEDICATION` et `PROTOCOL` ;
- ex. `extraction` doit pouvoir remonter le protocole correspondant ;
- choisir un protocole hydrate des lignes éditables, jamais verrouillées ;
- choisir un médicament hydrate l'identité catalogue puis laisse forme/dose/posologie modifiables.

### D5.5 — Personnalisation praticien / habitudes
- favoris et usages du praticien comme tie-breaker seulement ;
- aucun apprentissage depuis de simples impressions ;
- presets sauvegardent toutes les valeurs explicites de lignes ;
- recharger un preset reproduit les valeurs puis repasse par les guards Neo ;
- aucun signal d'usage ne peut dépasser une meilleure pertinence lexicale.

### D5.6 — Safety + provenance sans friction
- safety reste en arrière-plan / contextuelle ;
- aucune alerte ne doit remplacer les champs praticien ;
- aucune donnée RCP non vérifiée ne pilote la ligne ;
- modifications manuelles déclenchent revalidation sans suppression silencieuse de l'intention praticien.

### D5.7 — Certification UX
BEFORE / AFTER mêmes viewports : 390×844, 430×932, 768×900, 1280×900.
Tests obligatoires :
- médicament → édition complète ligne ;
- radio/examen → icône et comportement dédiés ;
- changement forme ;
- changement dosage ;
- posologie structurée + texte libre ;
- durée ;
- NS ;
- reorder/delete ;
- preset → édition ultérieure ;
- recherche DOLIPRANE ;
- recherche protocole extraction ;
- 200 % text scaling si harness disponible.

## Gate de sortie D5

D5 ne peut pas être fermé si :
- les 9 931 entrées ne sont pas réellement recherchables ;
- le ranking lexical régresse ;
- le praticien perd un contrôle historique sur une ligne ;
- les icônes / types Médicament et Radio-Examen disparaissent ;
- un preset ou protocole produit des lignes non éditables ;
- safety/catalogue efface silencieusement une personnalisation praticien.

Le closeout nécessite deux revues indépendantes internes avec scores sévères, plus validation visuelle AFTER.
