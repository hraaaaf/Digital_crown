# Digital Crown — Pharmacologie Maroc M1 — Internal continuation

Date: 2026-09-16
Status: ACTIVE — internal/documentary only

## Goal
Continuer M1 sans contact AMMPS et sans affaiblir le fail-closed réglementaire.

## Success
1. Les 7 familles Wave 1 restent explicitement non activées tant qu'aucun vrai RCP AMMPS conforme au contrat M1 n'est disponible.
2. Les identités réglementaires publiques déjà prouvées sont conservées séparément des données cliniques.
3. La chaîne future document → identité → bytes → SHA-256 → reviewer est prête et testable sans faux document.
4. Aucun `SNAPSHOT_VERIFIED`, `UNAVAILABLE_VERIFIED`, `AUTO_OK`, changement DB patient ou activation clinique n'est produit par ce lot.

## Décision propriétaire
Aucune demande, formulaire, email, appel ou autre contact AMMPS n'est autorisé. Toute réactivation exige une nouvelle autorisation explicite.

## État Wave 1
- paracetamol: fail-closed; identité AMMPS publique observée, aucun RCP cible capturé.
- ibuprofen: fail-closed; identité AMMPS publique observée, aucun RCP cible capturé.
- amoxicillin: fail-closed; présentations AMMPS exactes déjà identifiées, aucun RCP cible capturé.
- penicillin_v: fail-closed; identité AMMPS publique observée, aucun RCP cible capturé.
- metronidazole: fail-closed; présentations publiques observées, aucun RCP cible capturé.
- clarithromycin: fail-closed; présentations AMMPS observées, aucun RCP cible capturé.
- clindamycin: fail-closed; présentation systémique/orale courante utile non prouvée dans le pass actuel.

## Travail interne autorisé
- consolider les identités de présentation déjà prouvées et leurs références de provenance publique ;
- vérifier que les manifests/consommateurs ne transforment jamais un état pending en donnée clinique exploitable ;
- renforcer les tests négatifs du gate déterministe : document absent, URL non-AMMPS, hash faux, identité ambiguë, état pending ;
- préparer un fixture synthétique/non clinique pour tester la mécanique document → bytes → SHA → review sans prétendre à une preuve réglementaire ;
- documenter la procédure de promotion future, sans effectuer de promotion réelle.

## Interdits
- aucun contact AMMPS ;
- aucune URL RCP devinée ;
- aucun fallback ANSM/EMA comme preuve réglementaire M1 ;
- aucun RCP synthétique présenté comme officiel ;
- aucune activation clinique.

## Next exact
Inspecter sur master le manifest M1, le gate déterministe et leurs tests actuels; identifier le prochain gap interne réellement testable avant toute modification produit.
