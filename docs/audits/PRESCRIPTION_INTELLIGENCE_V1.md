# Prescription Intelligence V1 — Handover canonique

Date : 2026-09-14

## Statut

**OUVERT — audit d’architecture commencé, aucune logique de prescription intelligente implémentée à ce stade.**

Ce fichier est le point de reprise canonique du mini-chantier « ordonnance intelligente ».

## Goal

Permettre dans l’ordonnance un flux sécurisé de ce type :

`recherche médicament → sélection d’une présentation vérifiée → suggestion contextualisée si les données cliniques et la règle de dose sont suffisantes → calcul traçable → validation explicite par le praticien`.

Le système ne doit jamais transformer quelques lettres tapées en prescription clinique silencieuse ou non traçable.

## Succès observable

1. Une saisie partielle recherche des médicaments depuis une source locale/structurée vérifiée.
2. Le choix d’un médicament sélectionne explicitement une présentation/concentration connue.
3. Aucune posologie clinique n’est proposée si une donnée requise manque ou si aucune règle vérifiée n’existe.
4. Quand une règle est disponible, la suggestion expose les données utilisées, la formule/règle et le résultat.
5. Le praticien confirme avant que la proposition ne devienne le texte persistant de l’ordonnance.
6. Les scénarios négatifs sont testés : poids absent, indication absente, allergie/contre-indication pertinente, présentation inconnue, règle absente, donnée incohérente.

## Contraintes cliniques obligatoires

- Ne jamais déterminer une dose uniquement à partir de l’âge et du poids si la règle exige davantage de contexte.
- Ne jamais déduire silencieusement la voie d’administration depuis la forme galénique.
- Ne jamais inventer une concentration, une présentation ou une posologie absente de la source vérifiée.
- Les données nécessaires peuvent inclure selon le médicament : âge/date de naissance, poids, indication, allergies, fonction rénale, présentation/concentration et dose maximale.
- Toute proposition clinique doit rester une aide à la décision, avec validation finale du praticien.

## État Ordonnance déjà certifié

Le chantier UI précédent `DOCUMENT_STUDIO_ORDONNANCE_FIDELITY_V3.md` est **CLOS**.

Contrat existant certifié :

- `Prescription Composer V3.1` présent dans chaque `DrugRow` ;
- structure `Prise → rythme/condition → durée/limite → moment/durée → phrase synthétique` ;
- texte libre conservé en fallback ;
- persistance finale via `DrugItem.posologie: string` ;
- aucune inférence automatique de `voie orale` ;
- aucun moteur pharmacologique n’a été ajouté par V3.1.

Référence closeout : PR #474, merge commit `7607f759cf30d78df20de3d17bf0d361f11d2d36`.

## État repo vérifié au handover

Repo : `hraaaaf/Digital_crown`

Branche vérifiée : `master`

HEAD vérifié le 2026-09-14 :

`fdaa969f4369c7335e9badcd9480df223f8ee30c`

Dernier commit observé :

`feat(media): certify Competitive / Media C7 (#483)`

Aucun déploiement Vercel demandé ni réalisé pour ce mini-chantier.

## Audit déjà effectué

Repérage confirmé :

- frontend sous `frontend/src` ;
- fixture Ordonnance présente : `frontend/ordonnance-composer-fixture.html` ;
- arborescences pertinentes présentes : `frontend/src/components`, `frontend/src/features`, `frontend/src/data`, `frontend/src/services`, `frontend/src/types`, `frontend/src/pages` ;
- le canonical V3.1 confirme le contrat `DrugRow` / `DrugItem.posologie` et l’absence de moteur pharmacologique dans le lot UI précédent.

Ce qui **n’est pas encore vérifié** :

- fichier source exact du `DrugRow` courant ;
- modèle patient exact et disponibilité réelle de poids/allergies/fonction rénale/indication ;
- existence et qualité d’un formulary local exploitable ;
- éventuels services pharmacologiques existants ;
- règles de posologie déjà présentes ;
- couverture de tests exacte liée à ces éléments.

## Décision d’architecture

Découper l’implémentation en trois couches afin d’éviter le classique logiciel médical qui « devine » avec beaucoup d’assurance :

### A — Recherche médicament

Autocomplete déterministe depuis une source vérifiée. Aucun calcul de dose.

### B — Présentation

Sélection explicite de la forme/concentration disponible. Toujours aucun choix clinique automatique de dose.

### C — Suggestion clinique

Activée uniquement si :

- contexte requis complet ;
- présentation connue ;
- règle de dose vérifiée et versionnée ;
- garde-fous applicables ;
- résultat traçable et confirmé par le praticien.

Si l’un de ces éléments manque, afficher un état bloquant du type `Suggestion clinique indisponible : données/règle insuffisantes` plutôt que produire une posologie approximative.

## Aclav

Le nom `Aclav` a été utilisé comme exemple d’UX cible par l’utilisateur.

Ne pas hardcoder Aclav ni une posologie issue de mémoire. Il ne pourra servir de scénario de référence clinique qu’après vérification de la présentation exacte et des données officielles exploitables.

## Validation externe requise avant toute règle de dose

Pour une règle clinique, utiliser au minimum deux sources sérieuses et concordantes, primaires si possible :

- source réglementaire / RCP / AMM officielle ;
- source fabricant ou référentiel thérapeutique officiel adapté à la présentation exacte.

En cas de divergence, aucune règle automatique ne doit être activée avant résolution.

## UI/UX obligatoire si modification visuelle

`BEFORE → Goal écrit → référence/mockup → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel`.

Les viewports Ordonnance déjà utilisés comme repères sont : `390×844`, `430×932`, `768×1024`, `1280×900`.

## Handover de reprise

### Terminé

- Ordonnance Fidelity V3.1 certifiée et mergée séparément.
- Scope du nouveau mini-chantier défini.
- Principes de sécurité clinique définis.
- Repo et HEAD master vérifiés.
- Point canonique de reprise créé.

### En cours

- cartographie exacte du flux ordonnance et de la couche pharmacologique/formulary éventuelle.

### Restant

1. Re-vérifier `master`/HEAD au démarrage de la nouvelle fenêtre.
2. Identifier les fichiers exacts : `DrugRow`, type `DrugItem`, page/éditeur ordonnance, services/data médicaments, tests associés.
3. Auditer le modèle patient et l’origine de chaque donnée clinique requise.
4. Auditer les datasets/règles pharmacologiques existants.
5. Écrire le Goal/Succès/Preuve du lot A/B réalisable sans risque clinique.
6. Capturer le BEFORE si l’UI doit changer.
7. Implémenter d’abord A puis B avec tests et garde-fous.
8. N’implémenter C que pour une règle clinique vérifiée par sources concordantes et tests positifs/négatifs.
9. Lancer CI une fois le lot prêt ; corriger si nécessaire.
10. Mettre à jour ce fichier avec preuves exactes, commit/PR/runs et statut réel.
11. Aucun déploiement Vercel sans autorisation explicite.

## Next exact

**Identifier sur le HEAD courant les chemins et contrats exacts de `DrugRow`, `DrugItem`, du modèle patient et des sources/services médicaments, puis décider sur preuve si A/B peuvent être implémentés immédiatement et si C doit rester bloqué faute de référentiel clinique vérifié.**

## Blocage réel

Aucun blocage externe établi au moment de ce handover. L’accès GitHub via connecteur fonctionne ; seul l’accès réseau direct depuis le container avait échoué et n’est pas requis pour continuer.

## Critère de clôture du chantier

Le chantier ne pourra être marqué `CLOS` que si :

- code + tests + comportement observé sont cohérents ;
- garde-fous négatifs sont prouvés ;
- toute règle clinique implémentée dispose de sources vérifiées et traçables ;
- preuve UI avant/après existe si UI modifiée ;
- CI du HEAD final est verte ou les skips sont explicitement attendus ;
- ce canonique contient le commit/PR/runs exacts et le statut final réel.
