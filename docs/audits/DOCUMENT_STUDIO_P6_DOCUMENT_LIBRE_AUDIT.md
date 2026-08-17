# P6 — Document Libre : audit canonique exhaustif

## Baseline

- Branche audit : `agent/p4-p6-audit-baselines`.
- Baseline source : `master` à `026f78290cda53ea1b07ba5e8bfd39836448d6ce`.
- Portée : `LibreForm`, validation, toolbar, A4/A5, alignement, destinataire/date libre, preview, archive/réouverture, impression, PDF multi-page, permissions et protection de brouillon.
- **CODE VÉRIFIÉ** : oui pour les constats ci-dessous.
- **TESTS HISTORIQUES EXÉCUTÉS** : ancien socle P3-C a eu une CI verte ; les lots récents P3-D→P3-H ont été mergés avec jobs GitHub non exécutés avant runner selon le rapport historique.
- **TEST EXÉCUTÉ SUR CET AUDIT** : non revendiqué.
- **INTERACTION RUNTIME / VISUELLE** : non exécutée dans cette session.
- **CERTIFICATION PRODUCTION / RÉGLEMENTAIRE** : non revendiquée.

---

## 1. Architecture réelle P6

Flux principal :

`LibreForm.tsx` → état Document Studio → `useDocumentGenerator` → `/documents/generate` → `LibreData` → `LibreGenerator.generate()` → PDF → archive/réouverture.

Sous-flux : toolbar markup autorisé, tableau Markdown simple, format A4/A5, alignement, masquage en-tête patient, destinataire/date libre, dirty-state, preview et impression fraîche.

---

## 2. Matrice produit

### GARDER

1. Titre et contenu explicitement requis au générateur, avec bornes de taille.
2. Backend fail-closed sur format `A4|A5` et alignement autorisé.
3. Markup utilisateur échappé ; seule l'allowlist issue de la toolbar est conservée.
4. Balises autorisées déséquilibrées rendues sûres.
5. Tableaux Markdown rendus avec largeur bornée et en-tête répétable.
6. Noms de fichiers assainis.
7. Branding sous-compte résolu depuis le cabinet employeur.
8. Âge calculé à la date du document.
9. Document long multi-page sans compression microscopique.
10. Permission `clinical` requise pour émission/archivage/téléchargement.
11. Dirty-state sur les mutations de saisie + protection `beforeunload` et navigation inter-onglets.
12. Impression finale préparée depuis un PDF frais.
13. Archive réhydratable avec titre, contenu, destinataire, date/lieu, masquage en-tête, format et alignement.

### AMÉLIORER

1. La toolbar insère du markup visible (`<b>`, `<i>`, `<u>`, `<font...>`) dans un textarea : fonctionnel mais non WYSIWYG.
2. Bibliothèque de templates dédiée absente : amélioration produit, pas défaut de sécurité.
3. Accessibilité toolbar/format/alignement à recertifier au clavier et lecteur d'écran.
4. Preview vs rendu PDF : vérifier visuellement que l'utilisateur comprend que le textarea n'est pas un aperçu WYSIWYG exact.
5. Ergonomie petit écran 390/768 à recertifier, notamment les groupes Format/Alignement et la zone de rédaction.

### CORRIGER — P0

Aucun nouveau P0 statique démontré dans la baseline actuelle.

### CORRIGER — P1

#### P1-1 — certification finale absente
Les derniers lots Document Libre ont convergé en engineering mais les runs GitHub cités dans l'audit historique n'ont pas exécuté leurs steps. Il manque donc une régression réelle du head final.

**Décision** : ne pas déclarer P6 fermé tant que frontend/backend/PDF n'ont pas réellement tourné sur un head final identifiable.

#### P1-2 — runtime/rendu réel non certifiés
La sécurité du markup et du PDF est bien codée, mais il manque une inspection de PDF réels : A4/A5, texte long, tableau multi-page, caractères spéciaux, destinataire/date, hide header, alignements.

#### P1-3 — affordance « Grand Titre » limitée
Le bouton insère uniquement `<font size="16">`; ce n'est pas une hiérarchie documentaire complète. À classer amélioration UX, sans élargir arbitrairement l'allowlist HTML.

---

## 3. Contrat cible P6

Un Document Libre doit garantir :
- titre/contenu explicites ;
- aucun markup arbitraire interprété ;
- rendu PDF déterministe et lisible ;
- options de mise en page limitées à un contrat fermé ;
- patient/destinataire/date correctement échappés ;
- permission clinique ;
- aucun archivage lors d'une simple preview ;
- impression depuis un PDF frais ;
- round-trip archive → édition sans perte des champs supportés ;
- protection contre abandon involontaire du brouillon.

---

## 4. Connexions inter-pages

| Connexion | État code | Verdict |
|---|---|---|
| P6 → dossier patient | archive + réouverture | **GARDER** |
| P6 → impression | préparation PDF fraîche | **GARDER** |
| P6 → templates génériques | non branché dans le parcours actif | **OPTION PRODUIT** |
| P6 → autres pages | pas de conversion métier nécessaire démontrée | **NE PAS INVENTER** |

---

## 5. Lots canoniques restants

1. **P6-A — Régression finale réelle** : frontend/backend/PDF sur head final.
2. **P6-B — Runtime authentifié** : saisie, toolbar, tableau, A4/A5, alignement, preview, archive, réouverture, abandon protégé, impression.
3. **P6-C — Inspection PDF visuelle** : court/long/multipage/caractères spéciaux/tableaux.
4. **P6-D — Responsive / accessibilité** : 1440/768/390, clavier, focus et labels.
5. **P6-E — UX éditeur** : WYSIWYG/templates uniquement après certification, comme amélioration produit réversible.

---

## 6. Gates runtime encore ouverts

- titre/contenu vides et limites de taille ;
- `<`, `>`, `&`, markup arbitraire et balises déséquilibrées ;
- toolbar gras/italique/souligné/grand titre ;
- tableaux simples et multipage ;
- A4/A5 ; gauche/centre/droite/justifié ;
- destinataire/date libre et masquage en-tête ;
- preview sans archive ;
- archive + réouverture ;
- abandon protégé ;
- impression depuis PDF frais ;
- utilisateur sans permission clinique ;
- responsive et clavier.

**Verdict baseline : engineering fortement convergé, aucun nouveau P0 statique démontré, mais P6 reste non certifié final tant que ces gates réels ne sont pas fermés.**
