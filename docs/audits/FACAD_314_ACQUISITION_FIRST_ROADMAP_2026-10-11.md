# FACAD 3.14 — Roadmap unique réordonnée : ACQUÉRIR FACAD → CONSTRUIRE DIGITAL CROWN

**11 octobre 2026 — Decision utilisateur / Recherche autorisée d'abord, produit ensuite.**
**Périmètre :** science, interfaces, fonctions, formats et preuves de l'application FACAD 3.14.1.1111 par les voies autorisées, sans secret, licence bypass, patient ni réplication de code propriétaire. **Une seule checklist canonique Notion, pas de nouvelles cases duplicatives** : https://app.notion.com/p/3ec77c663362811db11ec59dbd9eb7d3 .

## Principe de séquencement

1. **PHASE F = FACAD ACQUISITION** : récolter et qualifier tout ce qu'on peut observer légalement et en sécurité sur FACAD, y compris comportements, analyses, dictionnaire de mesures, cas de référence, mises en page et exports seulement si autorisés.
2. **GATE TRANSFERT = FACAD KNOWLEDGE HANDOVER** : audit 65 profils + toutes les surfaces ciblées, provenance/hashes durables, registre de lacunes avec motifs et tentatives licites, autorisations et limites, revue du dossier complet. Si Ilexis refuse ou si sécurité non résolue, marquer précisément EXTERNAL_BLOCKER/NOT_TESTED ; ne JAMAIS présenter la fonction ou le calcul comme observé. La clôture du relevé possible doit être explicitement décidée.
3. **PHASE D = DIGITAL CROWN** : rouvrir les jalons CEPH produit, créer les fonctionnalités sur la base du pack FACAD et de sources scientifiques indépendantes, puis comparer les mêmes cas/mesures/UX quand le fournisseur et la sécurité l'autorisent. FAC-05 de parité n'est **pas** un préalable logique à la fin de la collecte FACAD : il nécessite Digital Crown.

**Compteur actuel :** FACAD **20/39 = 51,3 %** (20 jalons vérifiés, 19 ouverts). Ensemble Céphalo+FACAD **40/99 = 40,4 %**. Ces compteurs sont des cases MIXTES (collecte et parité), **pas** un indicateur d'exhaustivité de la collecte, et ne doivent pas être artificiellement gonflés pour atteindre 100 %. Un BLOCKED documenté n'est pas un PASS.

## État des lieux exact — données déjà capturées

- D0 : menus 9/9, origine/copie Robert integrity historique (mais ne prouve pas isolation applicative) ; F00.4 droits d'essai et conservation OPEN.
- D1 : **65/65 analyses et éditeurs observés** sous UIA ; définitions/mesures mathématiques et valeurs patient **non validées**. **42/65** profils ont les trois fichiers UIA CSV stricts dans Git à ref B65 ; **23/65** sans triplet Git au ref (certaines archives existent ailleurs, pas une absence FACAD). Exceptions Steiner run global partiel, Harvold Lines 0, alias Tübingen.
- Science : manifest C01 PDF 12 pages SHA `a977f219b6c9b95543551fe7a6e48587ac597b065e0200ab844e20ed322ba119` ; C02 PDF 34 pages SHA `4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548`. Un index lexical n'est pas la définition par page ; **9 types génériques** trouvés dans le manuel officiel FACAD 3.14 p86–87, pas les formules propres aux profils. F01.13 OPEN.
- D2 : 19/19 vues au niveau menus ; F02.2 Marker guide et Planned positions visibles (Toggle UIA « On ») sans action, F02.3 Tracing 10 commandes + View 20 commandes sans leaf ; **comportement d'action non testé**. F02.4 12 comparaisons candidates, **0 capture Digital Crown appariée au même cas/viewport**.
- D4 : onglets visibles `Values` et `Properties` avec capacités UIA sur run #38139444512 ; quatre autres noms `NOT_OBSERVED_IN_CURRENT_STATE` (ne veut pas dire inexistants). **Aucun Save/Load/Export, rapport FACAD ou contenu Properties certifié.**
- D5 : DC **56 tests de géométrie synthétique**, aucune parité numérique FACAD même tracé ; les rapprochements Steiner ML Go-Gn vs Tweed ML Go-Me, Ricketts Gn construit, ANB homonyme et E-line V1/V2 interdisent l'alias automatique.
- Archives : **65** runs GitHub identifiés ; **8** archives ZIP de profils + **1** archive CSV groupée listées dans le dossier Drive historique à cette date ; **57 autres profils non retrouvés dans CE dossier** (pas preuve d'absence ailleurs). Tous les ZIP Drive non relus octet/hachage, politique de conservation non signée.
- D3 : 6 BLOCKER SEC-01/02/03 et SCI-01/02/03, `D3_OPEN_RED`, licence/usage GitHub non certifiés, isolation réelle de stockage non démontrée, egress non approuvé, reviewers humains **0/2**. Nouveau FACAD natif et toute opération d'écriture sont suspendus en attente de droit et de protocole.

## PHASE F — parcours d'acquisition exhaustive, ordre de réalisation

### F-A / P0 — Paquet conservé et droits (F06.1, F00.4 et D3 SEC-01)
**Résultat :** une fiche par 65 analyses, avec run/commit/artefact/3 CSV/captures/CSV source-hashes/destination et statut `COMPLETE_VERIFIED`, `PARTIAL`, `NOT_AVAILABLE`, `RIGHTS_BLOCKED`. Récupérer légalement 23 triplets Git absents depuis preuves déjà existantes et archives autorisées ; vérifier octets Drive réellement, politique de rétention/destruction et titulaire de droits. Obtenir **une réponse écrite Ilexis** concernant environnement de test, UIA, lecture C01/C02, conservation des captures et cas non cliniques, **avant tout nouveau test natif**. Pas de publicité de fichiers propriétaires.

### F-B / P0 — Tour fonctionnel du logiciel (F02.2, F02.3, F04.1)
**Résultat :** carte des écrans/fonctions/propriétés, commandes navigation, tracing, hard/soft/teeth, layers/superimposition, marker guide, planned positions, analysis values/properties, positions/object values, options et préférences. Pour chaque commande : `SEEN_MENU`, `VISIBLE_UIA`, `BEHAVIOR_VERIFIED`, `NOT_OBSERVED`, `WRITE_RISK_BLOCKED`, avec vidéo/capture/UIA BEFORE/AFTER même viewport + SHA et cas non clinique. D'abord replay hors-ligne des artefacts, ensuite seulement expérience native **si autorisée et isolée**. Un menu présent ne certifie jamais son action.

### F-C / P0 — Atlas scientifique de FACAD (F01.13, préparation F05.1)
**Résultat :** table 65 profils × mesures réellement accessibles : nom exact, operator/arguments, construction C01, entrée C02 avec page, landmarks/lignes et conflits, formula/sens/angle/distance, mm/px, unité, signe, décimales, arrondi, norme uniquement si version/population/âge/sexes documentés, source primaire/SHA/version. Prios : Ricketts 32F/13F, Steiner, Tweed, McNamara, Downs ; pas de substitution de noms ni de copié-collé du PDF propriétaire. Définition de type ≠ formule d'analyse ≠ validation clinique. Chaque cellule `SOURCE_VERIFIED` ou `UNKNOWN` / `NOT_ALLOWED`.

### F-D / P1 conditionnel aux droits et D3 — Rapports, préviews, entrées/sorties (F04.2, F04.3, F04.4)
**Résultat :** captures autorisées de prévisualisation de rapports, champs et chapitres, formats de fichiers générés et classification `READ_ONLY` / `LOCAL_WRITE` / `SHARED_APP_WRITE` / `UNKNOWN` ; exemple Ricketts 32F/13F strictement non clinique, calibration et version exacte si légitime. **Aucun Export/Save/Load/ETW brut/donnée patient avant licence + isolation + confidentialité démontrées et autorisation distincte**. En cas de refus, documenter `EXTERNAL_BLOCKER` et rester source-only.

### F-E / P1 — Référentiel de cas FACAD exploitable après acquisition (composante vendor de F05.1)
**Résultat :** dossier de référence non clinique officiellement permis : image, coordonnées repères, identification analyses, calibration, orientation, mesures FACAD par cas si autorisées, labels, screenshot, sources et hash. Il **n'exige pas encore** la comparaison ni la modification de Digital Crown. Zéro cas patient.

### F-F / P0 à la fin — Handover d'acquisition FACAD (F06.2, F06.3, F06.4)
**Résultat :** tous les artefacts légaux en dépôt privé selon droits, inventaire complet et preuves d'accès, tableau **CE QU'ON SAIT / CE QU'ON NE SAIT PAS / POURQUOI / RETOURNABLE OU NON**, matrice source géométrique et UX, risque/dette, deux perspectives contradictoires **internes** clairement distinguées des vraies revues externes, décisions concernant les voies bloquées. F06.4 peut clore **seulement la campagne d'acquisition au périmètre réellement accessible**, avec dossier précis des items D3/D4/D5 toujours ouverts ; aucune fausse fermeture à 100 %.

## GATE TRANSFERT — conditions mesurables pour revenir à Digital Crown

- Chaque profil des **65** a une ligne d'inventaire liée à une preuve, un statut de source et ses manques ; pas de prétention `certified` lorsqu'une formule manque.
- Tous parcours/écrans prioritaires observables identifiés avec état d'activation réel, artefact ou blocage motivé ; mêmes viewports et version logicielle documentés lorsqu'ils ont été capturés.
- Liste des rapports, préviews, exports, valeurs et propriétés avec distinction `OBSERVED`/`UNKNOWN`/`PERMISSION_BLOCKED` et risque d'écriture.
- Les originaux et copies de référence sont protégés, artefacts licites et preuve de leur conservation/hash vérifiés ; aucun secret ni données cliniques.
- Les demandes aux tiers (Ilexis, sécurité, cliniciens) sont faites ou explicitement bloquées ; la décision utilisateur accepte le périmètre réellement récupéré. Les champs non observés restent `UNKNOWN`, **jamais PASS**.
- F06.3 revue de couverture et F06.4 décision formelle sur périmètre acquis, accompagnés du dossier `FACAD_EVIDENCE_PACK`. Pas de chiffrage « 100 % » sur tâches mélangées ou sur fonctionnalités inaccessibles.

## PHASE D — retour Digital Crown APRÈS transfert

1. Réconcilier `master`, PRs et branches pertinentes ; décongeler CEPH seulement après réception du dossier. Garder le travail V1.5 distinct.
2. Refaire la roadmap produit CEPH00–12 : reprendre les mesures source-justifiées, prioriser moteur déterministe CEPH06, science CEPH08, UX CEPH07, fichiers/PDF, mobile réel. Restreindre les normes cliniques inconnues.
3. Construire puis comparer **même cas/mêmes repères/échelle/mêmes versions** quand les droits et D3 l'autorisent : FAC-05 F05.2 (Ricketts), F05.3 (Steiner/Tweed/McNamara/Downs + UX/rapports), F05.4 (tickets CEPH), F02.4 (vue comparée CEPH07).
4. Tests automatisés, CI REQUIRED, comparateurs préenregistrés, revues scientifiques **humaines** pour usage clinique ; aucune certification de parité par captures ou tests synthétiques seulement.

## Suivi et statut au moment de ce plan

**Avant** : 39 cases FACAD mixtes, 20/39 validées et 19 ouvertes. **Après réorganisation** : mêmes 39 cases, aucun changement non justifié ; statut FACAD 20/39, D3 OPEN_RED, same-trace numerical parity NOT_TESTED, `CONVERGED=false`. **Aucun merge/deploy ni nouvelle expérimentation FACAD**. Le texte remplace l'ancienne interprétation « stop après WAVE 5 » ; il n'annule aucun test ni artefact.
