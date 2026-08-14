# Document Studio — cartographie exhaustive & refonte intelligente

## Objectif
Cartographier puis refondre intelligemment tout le module documentaire de Digital Crown sans perdre les fonctionnalités utiles ni le positionnement premium.

L’audit doit descendre au niveau **interaction par interaction** : clic, touche clavier, état avant/après, panneau/modal/table affiché, position, contenu, données utilisées, backend appelé, calculs, erreurs, transitions entre pages et effets secondaires.

## Règle de preuve
Pour chaque comportement, distinguer explicitement :
- **CODE VÉRIFIÉ** : comportement démontré par le code source.
- **TEST VÉRIFIÉ** : comportement couvert par un test identifié/exécuté.
- **INTERACTION EXÉCUTÉE** : comportement observé dans l’application réelle.

Ne jamais assimiler une lecture de code à un test UX réel.

## Format d’audit de chaque interaction
**Interaction → déclencheur → état avant → action → état après → élément affiché → position → contenu → données utilisées → backend/calcul → erreurs/edge cases → valeur UX → décision refonte.**

## Roadmap

### P1 — Ordonnance
- [ ] Saisie rapide, clavier et comportement de `Enter`
- [ ] Autocomplétion et sélection
- [ ] Presets intégrés
- [ ] Presets personnels / favoris
- [ ] Habitudes apprises / suggestions
- [ ] Bibliothèque médicaments
- [ ] Recherche et filtres bibliothèque
- [ ] Ajout/suppression/réorganisation d’un médicament
- [ ] Posologies et dosettes
- [ ] Adaptation âge / poids / contexte patient
- [ ] Validations médicament / dosage / alertes
- [ ] Conseils patient
- [ ] États vides, erreurs et fallback
- [ ] Preview / sauvegarde / impression / sortie
- [ ] Cartographie complète des appels backend et dépendances
- [ ] Verdict UX : garder / fusionner / cacher / refaire

### P2 — Devis + Honoraires
- [ ] Actes rapides / recherche catalogue
- [ ] Odontogramme : chaque interaction dent/groupe/schéma
- [ ] Déclenchement du tableau/panneau associé
- [ ] Position, contenu, sélection et validation de ce tableau
- [ ] Modes individuel / groupe / général
- [ ] Tarification et habitudes tarifaires
- [ ] Bundles / propositions complémentaires
- [ ] Organisation par phases
- [ ] Totaux et cohérence
- [ ] Honoraires : encaissement et modes de règlement
- [ ] États vides, erreurs, sauvegarde, preview, impression
- [ ] Verdict UX

### P3 — Certificat + Document Libre
- [ ] Types de certificats et transitions
- [ ] Durée / slider / motif
- [ ] Suggestions et mutations automatiques
- [ ] Preview / sauvegarde / impression
- [ ] Document Libre : toolbar, formatage, tableaux, contenu brut/rendu
- [ ] Templates / réutilisation
- [ ] États vides / erreurs / protection saisie
- [ ] Verdict UX

### P4 — Suivi Paiement / Échéancier
- [ ] Chargement plan existant
- [ ] Total / avance / nombre d’échéances
- [ ] Génération des lignes
- [ ] Arrondis et réconciliation exacte
- [ ] Modification manuelle
- [ ] Statut payé / non payé
- [ ] Rappels / WhatsApp
- [ ] Résumé payé / restant / prochaine échéance
- [ ] États vides, erreurs, sauvegarde
- [ ] Verdict UX

### P5 — Compagnon diagnostique + interactions inter-pages
- [ ] Arbre complet des états/questions
- [ ] Contexte patient utilisé
- [ ] Sorties diagnostic / actes proposés
- [ ] Validation praticien
- [ ] Passage Compagnon → Devis
- [ ] Passage vers Ordonnance / autres documents si prévu
- [ ] Conservation/perte d’état lors des changements d’onglet
- [ ] Fonctionnalités orphelines / callbacks non utilisés
- [ ] Verdict UX et positionnement dans le produit

### P6 — Audit transversal premium
- [ ] Navigation globale et ordre des onglets
- [ ] Header / Footer et actions globales
- [ ] Dirty state / autosave / protections navigation
- [ ] Preview responsive / split view / plein écran
- [ ] Responsive multi-format
- [ ] Typographie / tailles minimales / contraste
- [ ] Dark mode
- [ ] Raccourcis clavier
- [ ] Cohérence labels / terminologie / faux labels IA
- [ ] États loading / empty / error / success
- [ ] Accessibilité
- [ ] Cohérence clinique/financière/documentaire

### P7 — Refonte intelligente finale
- [ ] Cartographie consolidée du module
- [ ] Matrice **GARDER / AMÉLIORER / FUSIONNER / CACHER / SUPPRIMER / REFAIRE**
- [ ] Nouvelle architecture de navigation
- [ ] Hiérarchie de ce qui doit être visible en premier
- [ ] Wireflow fonctionnel cible
- [ ] Priorités P0/P1/P2 de refonte
- [ ] Plan d’implémentation par lots réversibles
- [ ] Critères de validation UX/fonctionnels
- [ ] Recertification finale du Studio documentaire

## État initial
- P1 : ⬜ à auditer en profondeur
- P2 : ⬜
- P3 : ⬜
- P4 : ⬜
- P5 : ⬜
- P6 : ⬜
- P7 : ⬜

Le précédent audit statique général sert uniquement de pré-analyse. Il **ne valide aucun sous-P** tant que la cartographie détaillée correspondante n’est pas terminée et double-checkée.

## Baseline de code
Audit détaillé lancé depuis la branche `master`, baseline observée : `c740b6644b4b85363438998dcf34284054122464`.
