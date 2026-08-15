# P1 — Ordonnance : cartographie exhaustive & plan de refonte

## Statut de preuve

Baseline auditée : `master`, application parent `c740b6644b4b85363438998dcf34284054122464` + documentation de roadmap.

- **CODE VÉRIFIÉ** : oui, frontend + backend + générateur PDF inspectés.
- **TESTS IDENTIFIÉS** : oui, tests frontend/backend existants recensés ; absence de test signalée lorsqu’elle est pertinente.
- **INTERACTION EXÉCUTÉE** : **non**. Aucun clic/clavier dans une instance réelle n’est certifié par ce rapport.
- **CERTIFICATION CLINIQUE** : hors scope. Les protocoles/doses sont inventoriés, pas approuvés médicalement.

## Score synthétique — audit statique

| Lot | Fonctionnalité | Intuitivité | Efficacité | Robustesse / prévisibilité | Hiérarchie premium | Score synthèse |
|---|---:|---:|---:|---:|---:|---:|
| P1-L1 Saisie rapide & clavier | 8.5 | 8.2 | 9.0 | 6.8 | 8.0 | **8.1/10** |
| P1-L2 Ligne médicament | 9.2 | 7.0 | 8.7 | 7.5 | 7.1 | **7.9/10** |
| P1-L3 Protocoles & habitudes | 9.0 | 6.8 | 9.0 | 5.5 | 7.0 | **7.5/10** |
| P1-L4 Référentiel médicaments | 9.0 | 7.4 | 8.4 | 7.6 | 7.6 | **8.0/10** |
| P1-L5 Âge / poids / pédiatrie | 8.0 | 6.5 | 8.0 | 5.5 | 7.0 | **7.0/10** |
| P1-L6 Sécurité & validation | 8.8 backend / 6.0 UI | 6.2 | 7.0 | 6.2 | 6.8 | **6.8/10** |
| P1-L7 Contexte patient & conseils | 8.0 | 6.0 | 7.2 | 6.5 | 6.4 | **6.8/10** |
| P1-L8 Sauvegarde / preview / impression / sortie | 8.0 | 7.2 | 7.8 | 5.5 | 7.5 | **7.2/10** |

**Score statique P1 Ordonnance : 7.4/10.**

Ce score mesure l’état UX/engineering observé dans le code, pas la sécurité clinique ni le comportement runtime réel.

---

## P1-L1 — Saisie rapide & clavier

### Parcours exact

1. Le champ affiche une saisie libre de type `Augmentin 1g sachet 2x/j`.
2. Chaque frappe met à jour `quickVal` et lance la recherche différée côté parent.
3. La recherche utilise le **premier token** du texte et interroge `/prescriptions/habits/suggest`.
4. Si des résultats existent, un dropdown absolu apparaît sous la barre (`top-full`, `z-[999]`).
5. `ArrowDown` / `ArrowUp` changent l’index surligné.
6. `Enter` :
   - si une suggestion est surlignée, elle remplace uniquement le premier token ;
   - sinon le texte courant est soumis ;
   - `parseQuickEntry` structure la ligne ;
   - `hydrateMedicationDetails` enrichit la ligne ;
   - le placeholder unique vide est remplacé, sinon la ligne est ajoutée ;
   - le champ est vidé ;
   - l’état passe à `PLANNING` ;
   - la saisie rapide se replie.
7. Clic sur suggestion : `onMouseDown + preventDefault`, puis même pipeline de soumission.
8. `Escape` remet seulement l’index à `-1` ; il ne ferme pas explicitement la liste.
9. `blur` remet l’index à `-1` après 200 ms.

### Points forts
- Saisie très rapide et compatible clavier.
- Sélection par `mousedown` protège contre la course blur/clic.
- Enrichissement automatique après parsing.

### Défauts
- Aucun verrou pendant l’hydratation async : doubles `Enter` rapides potentiellement dupliqués.
- `Escape` ne ferme pas réellement les suggestions.
- Recherche rapide limitée au premier token.
- Pas de fallback local de suggestions dans ce chemin si l’API échoue, contrairement à la ligne médicament.
- Tests existants centrés sur le clic suggestion ; `Enter`, flèches, Escape, blur, race async et hydratation ne sont pas couverts dans le test inspecté.

### Décision
**GARDER + RENFORCER.** C’est l’entrée primaire idéale.

---

## P1-L2 — Ligne médicament

### Contenu d’une ligne
- Monter / descendre.
- Type `Médicament` / `Examen`.
- Nom avec autocomplétion.
- Forme pharmaceutique + menu dédié en position fixe.
- Forme `AUTRE` éditable.
- Dosage.
- `NS` / non substituable.
- Posologie auto-height.
- Validation locale et référentiel national.
- Suppression.
- Overlay d’allergie pénicilline avec `Retirer` ou `Forcer sous votre responsabilité`.

### Dropdown médicament
- Ligne portée à `z-50` quand suggestions ouvertes.
- Overlay parent à `z-40`, donc dropdown reste cliquable.
- Ce comportement possède un test de régression identifié.

### Défauts
- Trop de commandes au même niveau visuel.
- Typographies fréquentes de 7–10 px.
- Plusieurs boutons icône reposent sur `title`, sans preuve d’un labeling accessibilité complet.
- Couverture de tests inspectée faible pour réordonnancement, NS, type, forme, force allergie, validation nationale et clavier.

### Décision
**GARDER LA PUISSANCE, REFAIRE LA HIÉRARCHIE.** Ligne compacte par défaut, détails progressifs.

---

## P1-L3 — Protocoles & habitudes

### Sources réellement présentes
1. Protocoles système codés localement.
2. Presets personnels (`DoctorPrescriptionPreference`).
3. Habitudes de prescription enregistrées.
4. Suggestions personnalisées de médicaments / dosages / posologies.

### Protocoles système inventoriés
- Avulsion Simple.
- Extraction Sagesse / Chirurgie.
- Abcès / Infection.
- Gingivite / Parodontite.
- Pulpite / Douleur Aiguë.
- Chirurgie Implantaire.
- KIN comme preset dédié.

### Défauts vérifiés
- **Suppression preset personnel cassée** : l’UI lit `DoctorPrescriptionPreference`, mais l’endpoint de suppression efface `DoctorActHabit`.
- `learn_habit` absorbe certaines erreurs DB après rollback ; le niveau appelant peut donc annoncer un succès sans persistance effective.
- `Masquer` la barre de protocoles met `showPresets=false` sans contrôle de réaffichage trouvé dans le composant inspecté.
- Backend de suggestion historique peut faire un fallback réseau vers `medicament.ma`, ce qui est incohérent avec un produit local/offline-first et ajoute dépendance/latence externe.

### Décision
**GARDER, FUSIONNER ET FIABILISER.** Présenter un seul concept utilisateur : **Mes protocoles** avec sources discrètes `Système`, `Personnel`, `Habitude`.

---

## P1-L4 — Référentiel médicaments

### Modal
- Plein écran au-dessus du Studio (`z-[40000]`).
- Âge et poids éditables.
- Recherche nationale.
- Catégories/règles curées.
- Ajout manuel.
- Résultats nationaux par nom commercial/DCI.
- Posologie éditable avant ajout.
- Fermeture après ajout.

### Référentiel national backend
- JSON local Maroc, chargé en mémoire.
- Recherche nom commercial ou DCI.
- Validation d’existence du dosage.
- Comparaison simple `MG` / `G`.
- Concentrations `mg/ml`, `%`, UI non comparées comme mg simple.
- Aucune posologie pédiatrique/CI dans ce dictionnaire : ces éléments vivent dans les règles cliniques curées.

### Défauts
- Un résultat national peut être ajouté même chez un enfant sans poids alors que les règles curées refusent correctement ce calcul.
- Les CI patient calculées dans le modal ne sont pas transformées en blocage/explication détaillée homogène dans chaque ligne.
- Ajout manuel possible avec seulement le nom.

### Décision
**GARDER + UNIFIER LE STATUT DE SÉCURITÉ.** Search-first, contexte patient visible en tête, même règle d’éligibilité quel que soit le chemin d’ajout.

---

## P1-L5 — Âge / poids / posologie pédiatrique

### Architecture sûre déjà présente
- `estimateWeightFromAge()` retourne actuellement `0` : aucune estimation implicite exploitable.
- `getAgeAwareDosing` exige un âge réel.
- Pour `<15 ans`, un poids réel positif est requis ; sinon `null`.
- Backend `prescription_context_guard` est fail-closed : âge, antécédents et poids enfant manquants rendent le contexte `non_evaluable` et aucune ligne automatique n’est proposée.

### Défaut majeur : trois chemins, trois comportements

**A. Saisie rapide**
1. preset local remplit les champs ;
2. règle âge/poids ne remplit ensuite que les champs encore vides ;
3. habitude complète les champs encore manquants.

Conséquence : un preset adulte déjà rempli peut empêcher la dose pédiatrique calculée de le remplacer.

**B. Sélection depuis autocomplétion de ligne**
- preset local d’abord ;
- puis règle âge/poids qui **écrase explicitement** dosage/posologie lorsqu’elle existe.

**C. Application d’un protocole système**
- transformations pédiatriques spécifiques hardcodées séparément.
- Exemple structurel trouvé : transformation `ANTADYS → PARACETAMOL 500MG` sans preuve que la posologie originale soit remplacée simultanément.

### Verdict
**P0 de cohérence.** Une même molécule ne doit jamais aboutir à une proposition différente selon le bouton utilisé.

### Décision
**REFAIRE LE PIPELINE, PAS LES RÈGLES.** Un seul moteur `normalizeMedicationForPatient()` utilisé par tous les chemins.

---

## P1-L6 — Sécurité & validation

### Trois couches présentes
1. **Heuristiques frontend** : dosage manquant, double antibiotique, AINS+corticoïde, double AINS, double paracétamol.
2. **Référentiel national** : médicament connu / dosage disponible.
3. **Backend safety** : antécédents, interactions, contexte clinique, antibiotique sans contexte chirurgical/endodontique, omissions, etc., avec garde tenant.

### Problème majeur de wiring
Le backend expose `/prescriptions/safety/check` et possède des tests dédiés, mais aucun appel frontend à cet endpoint n’a été trouvé dans le Studio ordonnance inspecté. Le badge visible `Sécurité Validée` est piloté par `coherenceWarnings`, donc principalement par les heuristiques/génération, pas par une preuve que tout le moteur safety backend a été exécuté.

### Autres problèmes
- Bannière rouge `Alerte Médicale & Allergies` apparaît dès qu’un texte d’antécédents existe, même s’il ne décrit pas une allergie.
- Le badge peut afficher `Sécurité Validée` simplement parce que la liste d’avertissements locale est vide.
- Substitution thérapeutique automatique en cas d’allergie dans `applyPresetWithSafety` : changement de médicament sans confirmation utilisateur explicite préalable. À convertir en proposition à accepter/refuser.
- Limites cliniques hardcodées dans certaines alertes frontend : nécessitent gouvernance scientifique séparée.

### Décision
**REFAIRE L’ORCHESTRATION DE SÉCURITÉ.** Un seul panneau de vérification, avec provenance de chaque contrôle et jamais le mot “validé” si tous les contrôles requis n’ont pas réellement tourné.

---

## P1-L7 — Contexte patient & conseils

### Comportement
- Assessment silencieux au chargement patient.
- Backend déterministe, pas LLM.
- États UI `RESEARCH → ASSESSMENT → PLANNING`.
- Bilan de risques / stratégie / suggestions moléculaires.
- Bouton `Établir l’Ordonnance`.
- Conseils patient repliables, champ libre.

### Défauts
- UI conserve `IAmina Intelligence`, `Agent`, `Intelligence Ghost Elite`, `Analyse du dossier`, alors que le moteur inspecté est déterministe.
- Bouton ↻ du header fait seulement `setStep('IDLE'); setAssessment(null)` ; aucun relancement explicite de l’assessment n’est attaché à ce clic.
- Messages comme `Sécurité Clinique Validée` sur absence de risques peuvent sur-promettre.

### Décision
**GARDER LE MOTEUR, RENOMMER L’EXPÉRIENCE.** `Contexte patient` / `Vérifications` / `Suggestions`, sans théâtre IA inutile.

---

## P1-L8 — Sauvegarde / aperçu / impression / sortie

### Enregistrer
- Footer → `onGenerate(true,false,false,false)`.
- Validation du payload.
- Analyse de cohérence frontend.
- POST `/documents/generate?archive=true&preview=false`.
- PDF produit.
- Archive patient créée.
- Puis apprentissage des habitudes ordonnance côté frontend si archive réussie.

### Imprimer
1. Footer `Imprimer` → demande de confirmation.
2. Modal annonce archivage automatique.
3. Confirmation → `onGenerate(true,true,false,true)`.
4. PDF généré/archivé.
5. iframe cachée utilisée pour déclencher l’impression ; fallback nouvel onglet.

### Aperçu
- Bouton footer ouvre un panneau latéral.
- Pour l’ordonnance, ouvrir le panneau ne génère pas automatiquement le PDF.
- L’état initial peut donc être `En attente de génération`.
- `Actualiser` dans le preview appelle `handleGenerate(false,false,true)`.
- Preview backend n’archive pas le document et ne journalise pas l’action de génération.
- Le test `test_document_preview_read_only.py` inspecté certifie actuellement la non-mutation DB pour **l’échéancier**, pas spécifiquement l’ordonnance.

### Défauts
- **Dirty-state ordonnance absent** lors du changement d’onglet et `beforeunload` : la garde existante ne protège que Devis/Honoraires.
- `hasChanges` est incomplet : update/suppression le marquent, mais plusieurs mutations directes via `setDrugs` (ajout rapide, presets, certaines additions) ne passent pas systématiquement par cette marque.
- `buildPayload` fournit silencieusement `forme: 'Sachets'` si une ligne médicament a une forme vide.
- Preview en double enveloppe visuelle : `DocumentHub` réserve/positionne 550 px puis `LivePreview` crée lui-même un portail fixe de 600 px. Architecture redondante et fragile responsive.
- Preview Ordonnance non auto-généré : clic `Aperçu` peut ouvrir un cadre vide, puis demande `Actualiser`.
- Skeleton preview affiche encore `Intelligence en cours...` alors qu’il s’agit de rendu PDF.

### Décision
**P0 dirty-state + P1 simplification du flux Enregistrer/Aperçu/Imprimer.**

---

# Défauts prioritaires

## P0 — correction avant cosmétique
1. Unifier le pipeline âge/poids/dose pour **toutes** les entrées médicament.
2. Supprimer toute substitution thérapeutique silencieuse : proposer → expliquer → praticien confirme.
3. Corriger suppression de preset personnel (`DoctorPrescriptionPreference`).
4. Propager l’échec réel de sauvegarde d’habitude/preset au lieu d’un succès possible après rollback.
5. Brancher réellement le moteur safety backend au flux ordonnance **ou** retirer/renommer toute affirmation `Sécurité Validée`.
6. Ajouter dirty-state universel ordonnance + marquage `hasChanges` sur toutes les mutations.
7. Corriger le bouton ↻ pour relancer réellement le contexte, ou le renommer `Réinitialiser`.

## P1 — expérience premium
8. Saisie rapide devient l’entrée #1, toujours accessible.
9. Ligne médicament en progressive disclosure avec taille typographique minimale lisible.
10. Fusion `Protocoles système + Mes ordonnances + Habitudes` sous **Mes protocoles**.
11. Référentiel médicaments search-first avec contexte âge/poids permanent.
12. Panneau de sécurité unique, provenance explicite des contrôles.
13. Nettoyer la terminologie IA devenue fausse/stale.
14. Preview intégré stable, pas double portail/fixed wrapper.

## P2 — efficacité
15. Récents/favoris sous la saisie rapide.
16. Couverture clavier complète et tests Enter/↑/↓/Escape.
17. Tests de non-régression multi-chemins : même molécule + même patient = même proposition normalisée.

---

# Plan de refonte en lots

## R1 — P0 Cohérence médicament
- Créer un pipeline unique d’hydratation/normalisation patient.
- Ordre de priorité explicite et testé.
- Tous les chemins (quick entry, ligne, protocole, bibliothèque, assessment) passent par lui.
- Aucune dose pédiatrique sans poids réel.
- Aucune substitution automatique sans confirmation.

**Gate :** matrice de tests multi-chemins avec résultats identiques.

## R2 — P0 Persistance protocoles/habitudes
- Corriger table de suppression.
- Corriger propagation des erreurs DB.
- Tests save/load/delete.
- Supprimer le fallback web implicite de suggestion ou le rendre explicitement optionnel/configurable ; défaut local-first = aucune dépendance web.

**Gate :** save → reload → delete → reload déterministe.

## R3 — P0 Safety orchestration
- Connecter `/prescriptions/safety/check` au Studio.
- Fusionner : règles locales + référentiel national + safety backend.
- État `non vérifié / vérification en cours / alertes / contrôles terminés`.
- Réserver `OK` à une liste définie de contrôles réellement exécutés.

**Gate :** tests allergies/interactions/contexte + tenant + UI state.

## R4 — P0 Dirty-state & actions
- Un wrapper de mutation pour tout changement d’ordonnance.
- Garde onglet + navigateur + reset.
- Corriger ↻.
- Éliminer le défaut caché `forme='Sachets'` ou le rendre explicite dans l’UI.

**Gate :** aucune mutation utilisateur non détectée.

## R5 — P1 Fast Prescription UX
- Saisie rapide persistante.
- Récents/favoris/protocoles en second niveau.
- Ligne compacte : Nom | Dose | Posologie | état sécurité.
- Forme/NS/type/examen sous détails rapides.
- Taille secondaire >= 12 px cible.

**Gate :** ordonnance simple en très peu d’actions sans perdre les fonctions avancées.

## R6 — P1 Protocoles + Référentiel
- `Mes protocoles` unifié.
- Source discrète et non technique.
- Masquer/réafficher réversible.
- Bibliothèque search-first.
- Contexte patient visible mais non envahissant.

**Gate :** aucune fonctionnalité actuelle perdue.

## R7 — P1 Contexte + Preview premium
- Remplacer les labels IA obsolètes par des libellés fonctionnels.
- Contexte patient compact en background avec alertes explicites.
- Preview unique en split-view responsive.
- Aperçu auto-généré/débouncé de façon read-only après données minimales valides.
- Actions finales : `Enregistrer` / `Imprimer`, sans ambiguïté.

**Gate :** preview read-only testé spécifiquement ordonnance + responsive.

---

# Hiérarchie cible

1. **Saisie rapide**
2. **Mes protocoles / récents**
3. **Ordonnance en cours**
4. **Alertes & vérifications**
5. **Ajouter depuis le référentiel**
6. **Conseils patient**
7. **Détails avancés**
8. **Aperçu / Enregistrer / Imprimer**

Le principe de refonte est donc : **ne pas retirer la puissance, retirer la concurrence visuelle entre les fonctions.**

---

## Addendum de recertification P1 — 2026-08-15

Cet addendum met à jour le statut de l'audit statique historique sans réécrire rétroactivement ses constats.

### État engineering / UX vérifié
- R1 → R7 sont fermés côté engineering selon leurs CI exact-head documentées.
- PR `#43` a corrigé les défauts responsive observés en runtime isolé et restauré la hiérarchie glass premium.
- Head final PR : `9a00f07c4b1dc98776cf03bc17b27c23b50d7a81` ; CI exacte `31898122575` — **SUCCESS**.
- Merge sur `master` : `91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8`.
- Comparaison historique pré-R1 : run `31897932430` — SUCCESS, artifact `9250318673`, digest `sha256:81db7ba5b525413908bb3b9faa84a2d6fc6478da756a6367b22d590c88e511e0`.
- Recertification finale glass : run `31898157179` — SUCCESS, artifact `9250378182`, digest `sha256:4809953baa1ed5dd49a7b143da694ae13e438394146a2d3c8809be90e39dd6de`.
- Vues inspectées : **1440 × 1100, 768 × 1100, 390 × 844**.
- Verdict visuel : aucune action principale rognée, aucun débordement horizontal destructif observé ; glassmorphisme conservé et hiérarchie contexte/sécurité regroupée.

### Constats historiques désormais corrigés côté engineering
Les sections plus haut décrivent la baseline auditée au moment de l'audit. Elles restent utiles comme historique, mais ne doivent plus être lues comme l'état courant pour : safety non branchée, dirty-state absent, fallback de forme implicite, UX rapide, protocoles/référentiel et preview responsive. Les preuves R1→R7 et PR #43 font foi pour l'état engineering actuel.

### Gates toujours ouverts
- **INTERACTION AUTHENTIFIÉE APPLICATION LOCALE : non certifiée.** Le harness rend les vrais composants mais n'est pas une session cabinet authentifiée.
- **CERTIFICATION CLINIQUE/PHARMACOLOGIQUE : non certifiée.** Revue qualifiée distincte requise.
- CI push exacte du merge `91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8` : run `31898590067` — à vérifier avant closeout documentaire final.

