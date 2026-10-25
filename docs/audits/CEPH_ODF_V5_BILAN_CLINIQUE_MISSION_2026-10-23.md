# DIGITAL CROWN — Mission V5 : vrai bilan orthodontique en 4 phases

**Statut : CAHIER D'IMPLÉMENTATION / NON IMPLÉMENTÉ** · **Date : 2026-10-23**  
**Demande propriétaire :** « Ce n'est pas du tout ça : un bilan ortho se compose de quatre phases : analyse céphalo (osseuse et dento-alvéolaire), examen des moulages, résumé diagnostique, plan de traitement. »  
**Dépôt :** `hraaaaf/Digital_crown` · **PR de diagnostic / habillage :** [#1048](https://github.com/hraaaaf/Digital_crown/pull/1048), toujours DRAFT et non fusionnée.  
**Baseline auditée avant mission :** `48232b20da6c2d27cceec3a25530761c1859d92a`. Ce document de mission ne certifie ni implémentation V5 ni activité clinique.

## 0. GOAL et écart de réalité

**GOAL :** PDF A4 intitulé « Bilan orthodontique », prêt à être relu par le praticien, avec exactement **quatre phases métier dans cet ordre** et l'identité documentaire du cabinet (cinq modèles, logo/QR, spécialités en haut, contacts et adresse en bas), sans code machine, compteur d'audit, « Mesure complémentaire 1, 2... » ni bloc de workflow.

**ÉCART VÉRIFIÉ :**
- `backend/services/cephalo_pdf_projection.py` construit seulement une **projection scientifique céphalométrique** issue de l'evidence graph typed + R15 ; il exclut expressément `ai_diagnostic`, `ai_narrative` et `clinical_data` comme autorités cliniques.
- `backend/services/generators/bilan_ortho_gen.py` et `backend/templates/bilan_ortho_authoritative.html` affichent ce modèle scientifique, pas un bilan ODF multimodal. La méthode `_clinician_measurement_label` crée des pseudo-libellés pour les identifiants non reconnus : pratique à **interdire**.
- `frontend/src/features/ortho/components/Step3Clinical.tsx` expose déjà les notes osseuses/dentaires, moulages, synthèse et stratégie ; `backend/schemas/clinical.py` a DDM, classes molaire/canine droite/gauche et champs narratifs. Mais le front avertit que ces notes, notamment historiques/importées, ont une **origine non vérifiée**. Les recopier automatiquement dans un document « validé » serait dangereux.
- `backend/services/generators/bilan_gen.py` est un ancien chemin basé sur `ai_diagnostic` et une classification historique non garantie ; il n'est **pas** un remplacement autorisé du pipeline R17, ni une source sûre de décisions thérapeutiques.
- `docs/audits/ORTHO_MODULE_V2.md` pose un **gate Ortho V2 après Céphalo-N**, provenance/praticien et modules multidisciplinaires. Ne pas contourner ce gate en appelant un PDF V5 « diagnostic prêt ».

## 1. Structure obligatoire du document

### PHASE 1 — Analyse céphalométrique
**A. Analyse osseuse / squelettique :** mesures sagittales (ex. SNA, SNB, ANB), verticales (ex. SN-GoGn, FH/Go-Me) et autres mesures autorisées par le contrat actif. Colonnes : **Mesure · Résultat · Référence** seulement si référence versionnée et applicable. Aucun diagnostic de classe squelettique extrapolé depuis un angle.
**B. Analyse dento-alvéolaire :** mesures maxillaires/mandibulaires et dentaires réellement disponibles (ex. U1/NA, L1/NB, IMPA, angle interincisif, surplomb/recouvrement si mesure autoritaire et méthode correcte). Ne pas confondre données de téléradiographie et observations occlusales issues des moulages. Éviter tout faux résultat normal ou « compensation » inférée.
**Règle** : registre explicite `measurement_id → nom métier + sous-rubrique + unité + convention/source` ; aucune ligne d'ID inconnu, aucune numérotation générée, aucune norme non sourcée, aucune valeur convertie/inventée. Les IDs non mappés sont enregistrés dans le rapport technique interne, **jamais** imprimés sous « Mesure complémentaire N ». Les vraies indisponibilités deviennent cellules sobres « Non calculable » lorsque la mesure elle-même est autorisée à figurer.

### PHASE 2 — Examen des moulages
Observations authentifiées : classe molaire et canine **droite/gauche**, forme des arcades, décalage des médianes et relation transverse si réellement renseignés ; DDM **maxillaire/mandibulaire** avec valeurs et unité, et espace disponible/nécessaire uniquement s'ils existent dans une source identifiée et vérifiée. Photos/scan seulement si média local autorisé, correctement lié au patient et à l'étude.
**Interdit** : DDM = 0 par défaut, interprétation d'encombrement déduite d'un champ vide, confusion DDM clinique / DDM instrumentée, inventer un examen des moulages à partir de la céphalo.

### PHASE 3 — Résumé diagnostique
Texte du **praticien**, restitué sans reformulation diagnostique automatique, structuré au besoin en constat osseux, dentaire/occlusal, anomalies et éléments associés. Une synthèse ne peut être marquée « validée » qu'avec preuve explicite auteur/horodatage/étude-révision et décision d'approbation du praticien.
**Interdit** : injecter `ai_diagnostic` ou notes historiques dans la partie validée ; inventer classe II/III, dysmorphose, gravité, étiologie ou indication de soin.

### PHASE 4 — Plan de traitement
Texte **rédigé ou expressément confirmé par le praticien** : objectifs, options retenues, séquence/étapes si décidées, remarques ou réserves réellement consignées. Les éventuelles options issues de R13 sont contextuelles, jamais traitées comme un choix de traitement par le système ; l'aval R14 est requis là où le gate canonique le prévoit.
**Interdit** : proposition thérapeutique autonome, appareils/extractions/durée/pronostic ajoutés sans décision documentée.

### Comportement si données manquantes
Dans l'aperçu **édition uniquement**, conserver les quatre titres et afficher au besoin « À renseigner par le praticien », sans codes ni grands encadrés d'audit. Un contenu absent ne doit jamais être comblé automatiquement. L'**export final patient/archivage** doit rester sous la gate clinique applicable ; ne pas faire passer un document maquetté ou incomplet pour un bilan diagnostique approuvé. Les contradictions et contre-indications cliniques avérées ne doivent pas être masquées.

## 2. Contrat de données et frontières d'autorité

Créer un **OrthoBilanDocumentProjectionV1**, en lecture seule et lié à `patient_id / analysis_id / revision`, avec `phases.cephalo.osseuse`, `phases.cephalo.dento_alveolaire`, `phases.moulages`, `phases.resume_diagnostique`, `phases.plan_traitement` ; chaque élément comporte, en données internes, `source_kind`, `source_id`, `author_id` si applicable, `validation_state`, `snapshot_revision`. Les champs de présentation ne deviennent jamais autorité. Aucune migration destructive, aucune duplication des valeurs céphalo.

**Ressources réutilisables, à auditer avant branchement :**
- `cephalo_pdf_projection.py` : mesures typées/profil R15 seulement.
- `cephalo_measure_registry.py` : catalogue `M_*` et statut de provenance ; vérifier explicitement les conventions exactes et l'exécutabilité.
- `schemas/clinical.py`, `Step3Clinical.tsx`, `useCephaloPersistence.ts` : champs moulages/narratifs déjà visibles/stockés, mais **autorité historique non confirmée** ; nécessitent un adaptateur *serveur* et preuve praticien par champ/snapshot.
- `document_factory.py`, `document_branding_contract.py`, `BaseTemplate`, générateurs HTML/ReportLab : identité document existante.

**STOP** : si aucune preuve backend de validation praticien ou aucun lien à la bonne étude/révision, ne pas faire de phase 3/4 « complétée » ou « signée ». Créer une tâche de persistance/validation dédiée sous le gate Ortho V2, pas une lecture opportuniste du store React ni du `clinical_data` injecté par la requête PDF.

## 3. Exécution séquencée, avec gates

**V5-G0 — audit domaine/sources :** inventaire champ par champ `PHASE | source exacte | authorité | persistance | version | lisible en PDF oui/non | dépendance`, status réel des notes/données, contrôle des endpoints et de l'archivage. Décision d'architecture avant code métier.  
**V5-G1 — projection métier fail-closed :** DTO quatre phases et mapping strict des mesures, assertions d'intégrité patient/étude/révision ; tests négatifs ID inconnu/mauvaise source/indisponible.  
**V5-G2 — notes de moulages et textes praticien :** transport strict depuis un snapshot versionné avec acteur vérifié, sans conversion des notes legacy en avis cliniques validés. S'il manque le contrat d'approbation, ne réaliser qu'un aperçu synthétique conditionnel.  
**V5-G3 — deux moteurs d'impression :** WeasyPrint + ReportLab, ordre quatre phases ; mêmes composants de branding que l'ordonnance. Supprimer l'ancien inventaire déversé, tous les labels « mesure complémentaire », les bandeaux d'audit, stages/gates techniques et termes anglais machine. Ne jamais effacer une alerte médicale réelle.  
**V5-G4 — parcours FUE authentifié :** deux patients/études *synthétiques* distincts, vrai JWT en environnement isolé, contrôle de l'étude/révision verrouillées, brouillon vs archive, fail-closed en cas de changement d'étude pendant génération, aucune donnée inter-cabinet.  
**V5-G5 — revue visuelle :** 5 styles `Swiss/Royal/Clinical/Modern/Heritage` en A4 + ordonnance A5, avec cabinet fictif complet Dr Salma Atlas, spécialité, logo, adresse, contacts, QR sur pages adéquates. Captures première/intermédiaire/dernière page ; aucun orphelin, collision, texte tronqué ni espace artificiel. Demander une validation de forme au dentiste propriétaire.

## 4. Critères d'acceptation NON négociables

1. Le sommaire et le PDF respectent l'ordre **1 Céphalométrie (osseuse / dento-alvéolaire), 2 Moulages, 3 Résumé diagnostique, 4 Plan de traitement** ; aucune section d'audit en substitution.
2. Zéro `Mesure complémentaire [nombre]`, zéro ID `M_*` brut, zéro `NOT_COMPUTABLE`, `source-lock`, `R11-R14`, compteur « lignes de mesures » ou bandeau de workflow dans le PDF praticien.
3. Zéro diagnostic, référence chiffrée ou traitement inventé. Les données non validées restent non validées dans le backend, même si leur statut interne n'est pas imprimé.
4. Deux cas synthétiques : (A) **toutes phases documentées et explicitement approuvées par un acteur fictif au moyen d'une fixture de validation** ; (B) champs/snapshot absents, aperçu incomplet **sans export patient faussement validé**. Cas défavorables : source contradictoire, mauvais patient, mauvaise révision, texte historique non attribuable, média introuvable, QR désactivé.
5. Tests binaires extrayant texte/objets réels PDF, comparant le contrat des quatre phases, QR / pied de page, pagination, fallback et absence des expressions interdites ; revue **humaine** des PNG après CI ; FUE authentifié vert au HEAD exact.
6. Pas de merge ni de déploiement sans décision explicite. **`CEPH_DETECTOR_SELECTED=NO`, Ricketts HOLD, clinical NO-GO, roadmap 41/99 inchangés tant que les gates correspondants ne sont pas réellement franchis.**

## 5. Livrables attendus

- Inventaire G0 des sources et lacunes d'autorité.
- Nouveau contrat `OrthoBilanDocumentProjectionV1`, mapping measurement IDs, deux renderers.
- PDF comparatifs réels **AVANT / APRÈS** sur les cinq styles + captures multi-pages + preuve des 4 phases.
- Logs/tests/PDF d'un FUE authentifié à études synthétiques distinctes.
- Documentation du mode aperçu/final et gate de signature.
- Handover Notion exact HEAD, PR DRAFT et décision explicite GO/NO-GO.

### Décision / limite

Cette mission **ne demande pas un nouvel algorithme diagnostique**. Elle demande de **réassembler correctement des faits cliniques et des décisions explicitement attribuées au praticien**, dans le bon ordre, sous la même identité de cabinet. L'Ortho V2 complet et son gate restent distincts : si une dépendance n'est pas réellement disponible, signaler BLOCKED plutôt que lui fabriquer une donnée ou déclarer le bilan V5 prêt.
