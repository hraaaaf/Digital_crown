# ⚠️ ANTIGRAVITY - Journal des Erreurs à ne plus commettre

Ce document répertorie les faux-pas techniques et ergonomiques identifiés lors du développement de Digital Crown, afin de garantir une qualité de code et d'UX constante.

---

### 1. Ergonomie & UI
- **[ERREUR] Contrastes Faibles** : Saisie de montants financiers en gris clair sur fond bleu/gris pâle.
- **[CORRECTION] Standard "High-Contrast"** : Tous les inputs financiers doivent impérativement utiliser `text-slate-950` (noir intense) avec `font-black` (extra-gras) sur fond `bg-white` (blanc pur).
- **[LEÇON]** : La lisibilité des chiffres (prix, dosages) prime sur l'esthétique du design glassmorphism.

### 2. Architecture Frontend
- **[ERREUR] Logique de Saisie Double** : Le formulaire de prix était défini deux fois (une fois dans `TreatmentSelector.tsx` et une fois en interne dans `Odontogram.tsx`). Le premier correctif n'a donc pas touché l'interface réellement utilisée par le praticien.
- **[CORRECTION] Centralisation des Styles** : Utiliser des constantes de classes CSS ou des composants de saisie atomiques pour garantir que tout changement visuel s'applique partout.
- **[LEÇON]** : Toujours vérifier s'il existe plusieurs "portes d'entrée" (Popover vs Modal) pour une même fonctionnalité avant de valider un correctif.

### 4. Performance & Ciclo de Vie React
- **[ERREUR] Composants définis dans le corps du parent** : `LiveDocumentStudio` était défini à l'intérieur de `SetupWizard`. Cela forçait React à recréer le type du composant à chaque render, neutralisant tout cache et causant des lags.
- **[CORRECTION] Extraction Hors-Corps** : Toujours définir les sous-composants en dehors du composant principal (ou dans un fichier séparé) et passer les données via des props.
- **[LEÇON]** : Ne jamais définir un composant React à l'intérieur d'un autre composant. Utiliser `React.memo` sur les sous-composants extraits pour une optimisation maximale.

---
*Dernière mise à jour : 2026-04-18 (Session v4.0)*
