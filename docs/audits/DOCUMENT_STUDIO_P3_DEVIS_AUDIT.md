# P3 — Devis : audit canonique exhaustif

## Baseline

- Branche audit : `agent/p3-devis-audit-baseline`.
- Baseline source : `master` à `026f78290cda53ea1b07ba5e8bfd39836448d6ce` (merge PR #72).
- Portée : page P3 Devis, odontogramme, tableau généré, recherche catalogue, actes rapides, bundles, phases, preview/PDF, archive et connexions P1/P4/P5/P7.
- **CODE VÉRIFIÉ** : oui pour les constats ci-dessous.
- **TESTS HISTORIQUES EXÉCUTÉS** : socles anciens P2-A/P2-C/P2-D/P2-E déjà mergés et CI verts selon la roadmap canonique.
- **TEST EXÉCUTÉ SUR CET AUDIT** : non revendiqué.
- **INTERACTION RUNTIME / VISUELLE** : non exécutée dans cette session.
- **CERTIFICATION CLINIQUE / FINANCIÈRE / PRODUCTION** : non revendiquée.

Cet audit distingue ce qui fonctionne, ce qui doit être amélioré et les défauts structurels. Une CI verte historique n'est jamais utilisée comme preuve d'un parcours runtime actuel.

---

## 1. Architecture réelle P3

Flux actif :

`DocumentHub.tsx` → `AccountingStudio.tsx` → `AccountingStudioLegacy.tsx` → `useAccountingStore` → `useDocumentGenerator.ts` → `/documents/generate` → `DocumentFactory.create_devis()` → `AccountingGenerator.generate_devis()` → archive patient.

Sous-flux principaux :
- actes rapides / habitudes ;
- recherche catalogue dans le tableau ;
- odontogramme adulte/enfant ;
- modes `individual`, `group`, `ortho` (libellé UI « Soins Généraux ») ;
- `TreatmentSelector` par dent ;
- bundles complémentaires ;
- organisation par phases ;
- tableau financier ;
- preview PDF ;
- archive / impression ;
- état partagé avec P4/P5 ;
- callback annoncé P7 → P3.

---

## 2. Matrice produit

### GARDER

1. **Actes rapides explicites et tactiles** : bouton d'ouverture réel, pas de dépendance au hover pour ouvrir la zone.
2. **Recherche catalogue principale** : le wrapper `AccountingStudio.tsx` répare bien les prix locaux via `AccountingActSuggestionPolicy`; l'ancien P2-A reste effectivement branché.
3. **Remplacement odontogramme idempotent par dent** : clé stable `dent::traitement`, autres dents et lignes manuelles préservées.
4. **Prix groupé inconnu fail-closed** : un groupe sans prix positif n'est pas ajouté silencieusement à `0 MAD`.
5. **Organisation par phases idempotente à l'écran** : les anciens séparateurs sont retirés avant reconstruction.
6. **Total principal déterministe** : UI et PDF additionnent une fois le prix de chaque ligne.
7. **Séparation Devis / encaissement** : l'archivage d'un devis ne crée pas d'`Acte` facturé ni de `Payment`; il archive le document et alimente seulement l'historique d'usage.
8. **Contrôle d'accès backend** : permission document + accès patient sont vérifiés avant génération.
9. **Abandon vers une page non comptable** : modale explicite avant effacement du panier.
10. **Conflit d'archive** : le doublon peut être refusé puis forcé explicitement.

### AMÉLIORER

1. **P3 ↔ P4** : le passage Devis → Note Honoraires est aujourd'hui un simple changement d'onglet avec état partagé. Le rendre explicite (« convertir/reprendre ce devis »), avec origine et confirmation visibles.
2. **Réordonnancement des lignes** : aucune vraie réorganisation manuelle n'est disponible malgré la richesse du tableau.
3. **Suppression tactile** : l'action supprimer du tableau est masquée par `opacity-0` jusqu'au hover ; elle doit rester découvrable sur tactile/clavier.
4. **Bundles** : garder la suggestion complémentaire si elle apporte une vraie valeur, mais avec une seule implémentation et une origine/prix clairs.
5. **Preview** : conserver la preview réelle backend/PDF, mais rendre le split responsive.
6. **Numéro, validité et signature** : les blocs peuvent être utiles, mais doivent être alimentés par un vrai contrat métier au lieu d'éléments visuels orphelins.

### CORRIGER — P0

#### P0-1 — contamination P5 → P3
`DocumentHub` charge automatiquement le dernier échéancier du patient dans le store partagé, quel que soit l'onglet actif. `useDocumentGenerator` transmet ensuite `installments` au payload Devis. Le PDF Devis rend ces données sous « ÉCHÉANCIER PRÉVISIONNEL ».

**Conséquence** : un ancien échéancier P5 peut apparaître silencieusement dans un nouveau P3 Devis. Le backend n'impose aucune réconciliation Devis entre total et échéances.

**Décision** : P3 ne doit recevoir aucun échéancier implicite. Un échéancier Devis futur devra être explicitement créé dans P3 avec son propre contrat et sa réconciliation.

#### P0-2 — colonne Dent ≠ dent réellement imprimée
Une ligne odontogramme/groupée transporte `toothNumbers`. La colonne `Dent` reste pourtant librement éditable. Le payload envoie les deux valeurs et le PDF privilégie `dents`/`toothNumbers` lorsqu'ils existent.

**Conséquence** : le praticien peut modifier la dent visible dans le tableau sans modifier la dent imprimée.

**Décision** : une seule source de vérité. Pour une ligne structurée, la dent doit être modifiée via l'odontogramme ou toute édition textuelle doit synchroniser atomiquement la structure.

### CORRIGER — P1

#### P1-1 — round-trip odontogramme incomplet
`AccountingStudioLegacy` reçoit `setSelectedTeethFromOdontogram` dans son contrat mais ne le destructure pas et ne l'appelle pas. `teeth_data` est donc vide pour un devis nouvellement construit par l'odontogramme. À la réouverture d'un devis archivé, `DocumentHub` reconstruit seulement les lignes plates et ne restaure ni `_odontogramKey`, ni catégorie, ni surfaces/notes.

**Conséquence** : le PDF principal peut montrer les dents via les lignes, mais le devis ne se réouvre pas comme un vrai plan odontogramme éditable.

#### P1-2 — prix catalogue perdu dans `TreatmentSelector`
Le catalogue principal conserve son prix grâce à P2-A, mais la modale odontogramme transforme les actes sans `base_price`. Le prix devient `PriceBrain.suggestPrice(name) || 0`.

**Conséquence** : une même prestation peut avoir son tarif catalogue dans le tableau principal et un ancien prix local ou `0` dans la modale dentaire.

**Décision** : priorité de prix unique : tarif catalogue explicite → prix praticien explicitement choisi → jamais une mémoire locale silencieuse à la place du catalogue.

#### P1-3 — surfaces et notes incohérentes
`TreatmentSelector` possède l'état et la fonction de surfaces mais ne rend aucun contrôle de surface. L'odontogramme P3 est monté avec `hideSurfaces=true` et `onSurfaceClick` vide. Les « Notes Cliniques » sont visibles et envoyées par `onConfirm`, mais le parent ignore `notes`.

**Décision** : soit connecter et persister surfaces/notes de bout en bout, soit retirer les contrôles non fonctionnels. Aucun faux affordance.

#### P1-4 — mode Enfant seulement cosmétique
Le dessin accepte la denture pédiatrique, mais `TreatmentSelector` est typé uniquement sur `ToothNumberFDI` permanent ; le parent contourne avec `as any`. Les raccourcis Q1–Q4 / S1–S6 restent codés en dents adultes.

**Décision** : denture pédiatrique complète de bout en bout ou masquer le mode jusqu'à implémentation réelle.

#### P1-5 — phases modélisées comme fausses prestations
« Organiser par phases » injecte des lignes `--- PHASE ... ---` à `0 MAD` dans le même tableau financier. Elles partent au backend/PDF et peuvent entrer dans l'apprentissage des actes.

**Décision** : phase = métadonnée/présentation, jamais `DevisItem` facturable.

#### P1-6 — apprentissage d'actes surpondéré
Un clic « Acte rapide » appelle immédiatement `/accounting/record-act`. L'archivage Devis réenregistre ensuite chaque ligne côté backend, puis le frontend les renvoie encore à `/accounting/record-act` après succès.

**Conséquence** : un acte cliqué puis supprimé est appris ; un acte archivé peut être compté plusieurs fois.

**Décision** : source autoritative unique = archivage réussi. Aucun apprentissage sur simple sélection.

#### P1-7 — suggestion RDV automatique non contractuelle
Après un document financier contenant certains mots (`ortho`, `contention`, etc.), le backend peut renvoyer « Planifier le prochain RDV dans 4 semaines » sur une durée codée en dur.

**Décision** : retirer cette recommandation de P3. Toute connexion agenda/suivi doit être un flux explicite basé sur des données et règles validées.

#### P1-8 — backend Devis trop permissif
`DevisData` accepte des listes vides, prix par défaut à `0` et échéances sans validation P3 dédiée. Les validations UI ne constituent pas une frontière serveur.

**Décision** : contrat backend fail-closed sur lignes, montants finis/plafonds raisonnables et invariants de structure. Les échéances implicites doivent être interdites.

#### P1-9 — PDF long dégrade la lisibilité
Le générateur A5 compresse la mise en page dès plus de six lignes. Une seule cellule longue peut imposer la taille minimale calculée à toute la table, avec `min_fs=2.0`.

**Décision** : privilégier wrapping et multi-page propre. Fixer une taille minimale lisible ; ne jamais « réussir » un PDF en rendant tout microscopique.

#### P1-10 — P7 → P3 orphelin
`DocumentHub` fournit `onConvertToQuote` à `TreatmentPlanStudio`, mais le composant P7 le renomme `_onConvertToQuote` et ne l'utilise pas.

**Décision** : implémenter une conversion explicite et contrôlée dans le tour P7, avec prix non inventés, ou supprimer le faux câblage en attendant.

#### P1-11 — preview non responsive
Quand la preview est ouverte, l'espace de travail réserve `pr-[570px]` et le panneau preview est `fixed` avec `w-[550px]`, sans breakpoint dans ce shell.

**Décision** : desktop split ; tablette/mobile overlay ou plein écran. À recertifier visuellement en 1440 / 768 / 390.

#### P1-12 — odontogramme non clavier-accessible
Les zones de dents sont des éléments SVG cliquables, sans rôle bouton, `tabIndex`, libellé accessible ou activation clavier.

**Décision** : focus/Enter/Space + nom de dent accessible + état sélectionné.

### SIMPLIFIER / SUPPRIMER

1. **Logique `insights` fantôme dans `DocumentHub`** : elle appelle bundles et construit plusieurs suggestions/alertes, mais seul le type `Insight` est importé et aucun composant ne rend cette collection dans l'arbre actif. Supprimer ou déplacer vers la page qui la possède réellement.
2. **Double moteur de bundles** : conserver uniquement le moteur visible de P3 ou une architecture partagée unique.
3. **Label « Assistant Intelligence » dans `TreatmentSelector`** : la logique observée est catalogue + mémoire locale déterministe. Employer une terminologie fonctionnelle.
4. **Durée `30 min` injectée à tous les actes catalogue de la modale** : ne pas afficher de durée sans donnée réelle.

---

## 3. Tableau odontogramme — contrat cible

Chaque ligne issue de l'odontogramme doit avoir :
- identifiant stable ;
- acte/catalogue source ;
- dent(s) structurée(s) ;
- surfaces structurées si utilisées ;
- notes si elles font partie du produit ;
- prix avec provenance explicite ;
- catégorie ;
- phase en métadonnée séparée ;
- capacité de round-trip archive → réouverture sans perte.

Règle : le texte affiché, le payload, l'archive et le PDF doivent être quatre vues de la **même donnée**, pas quatre versions concurrentes.

---

## 4. Connexions inter-pages

| Connexion | État code | Verdict |
|---|---|---|
| P3 → P4 Note Honoraires | État partagé, switch direct | **AMÉLIORER** : conversion explicite |
| P5 → P3 échéancier | Chargement global implicite | **P0 CORRIGER** |
| P7 → P3 Compagnon | Callback fourni mais non utilisé | **P1 CORRIGER** |
| P3 → agenda/suivi | Suggestion 4 semaines codée en dur | **SUPPRIMER de P3** |
| P3 → P1 Ordonnance | Pas de flux P3 fiable actif identifié | **À concevoir seulement si valeur réelle** |
| P3 → dossier patient | Archive PDF + clinical_data | **GARDER**, puis réparer le round-trip structuré |

---

## 5. Lots correctifs canoniques

Ordre par chemin critique :

1. **P3-A — Isolation financière Devis** : stopper contamination P5, interdire échéances implicites, renforcer contrat backend.
2. **P3-B — Source de vérité odontogramme/table** : dents, `teeth_data`, surfaces, notes, hydration/round-trip.
3. **P3-C — Prix/catalogue + modes odontogramme** : prix cohérents dans toutes les entrées, pédiatrique réel, groupes/secteurs.
4. **P3-D — Phases / bundles / apprentissage** : phases non financières, un seul bundle engine, apprentissage unique après archive.
5. **P3-E — Connexions inter-pages** : P3↔P4 explicite, neutralisation RDV automatique, contrat P7→P3 préparé sans prix inventé.
6. **P3-F — PDF professionnel** : lisibilité devis longs, numérotation contractuelle, signature réellement branchée si retenue, cohérence écran/PDF.
7. **P3-G — UX / responsive / accessibilité** : tactile, clavier, preview 1440/768/390, dirty-state et actions globales.
8. **P3-H — Recertification finale** : tests ciblés + régression, runtime authentifié, PDF réels inspectés, preuves séparées engineering/financier/clinique.

Les lots peuvent être subdivisés si une correction révèle un risque plus étroit. Leur fermeture nécessite des preuves réelles ; aucune pondération artificielle n'est utilisée pour produire un pourcentage.

---

## 6. Gates runtime encore ouverts

À exécuter sur l'application réelle :
- état initial P3 ;
- acte rapide puis suppression sans archivage ;
- recherche catalogue et prix ;
- clic dent adulte + réouverture ;
- denture enfant ;
- groupe Q/S et sélection libre ;
- modification Dent/Prix/Description ;
- devis long ;
- preview 1440/768/390 ;
- archive puis réouverture ;
- impression ;
- navigation dirty-state, reload et retour ;
- passage P3↔P4 ;
- patient possédant déjà un plan P5 ;
- inspection PDF et cohérence exacte total/dents/échéances.

---

## Verdict baseline

P3 possède un **bon noyau ergonomique et technique**, notamment les actes rapides, le catalogue principal, la déduplication odontogramme, les groupes et l'archive. Mais plusieurs sous-flux partagent des données sans frontière nette. Les défauts les plus graves ne sont pas cosmétiques : ils touchent la cohérence du PDF, l'isolation P5/P3, le round-trip odontogramme et la source des prix.

**État actuel : audit statique exhaustif consolidé ; corrections et runtime non fermés.**
