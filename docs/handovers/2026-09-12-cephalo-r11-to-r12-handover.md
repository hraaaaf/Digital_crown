# HANDOVER — CÉPHALOMÉTRIE — R11 → R12

Date : 2026-09-12  
Repo : `hraaaaf/Digital_crown`

## R11 — ÉTAT

**R11 Diagnostic multiaxial : FERMÉ côté implémentation.**

Goal R11 : `findings → hypothèses explicables`, contradictions et données manquantes visibles, aucune conclusion patient non sourcée.

### Preuves certifiées

- branche implémentation : `feat/cephalo-r11-diagnostic-multiaxial`
- candidate HEAD : `6916dee975acb83d13acd540d5d2e4a8f839a478`
- CI : #3477 — SUCCESS
- T2 Runtime Browser Certification : #2452 — SUCCESS
- PR implémentation : #437
- scope PR : 7 fichiers, branche ahead 21 / behind 0 avant merge
- reviews : 0
- commentaires PR : 0
- merge implementation : `bc66b58b6ee4459362d3bd52150877908bdc996c`
- master post-merge implementation vérifié : `bc66b58b6ee4459362d3bd52150877908bdc996c`
- déploiement : aucun

## CONTRAT SCIENTIFIQUE R11 FERMÉ

Chaîne autorisée :

`measurement evidence → contexte normatif optionnel → finding → diagnostic hypothesis → contradictions/missing data → validation praticien ultérieure`

Invariant :

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Décisions fermées :
- rule registry findings/diagnostics versionné et source-bound ;
- registre production diagnostique volontairement vide ;
- aucune règle clinique activée par simple nom/convention ;
- supporting/opposing exige une preuve `AVAILABLE` ;
- mesure indisponible → aucune évaluation normative `AVAILABLE` ;
- finding indisponible → ne peut soutenir/opposer une hypothèse ;
- missing refs doivent réellement représenter une absence/indisponibilité, sauf contexte normatif inactif explicitement bloqué ;
- inactive norm → jamais support/opposition d'un finding et aucune classification patient ;
- overlap supporting/opposing rejeté ;
- `NOT_COMPUTABLE` et `INSUFFICIENT_DATA` restent explicites ;
- aucune indication, option thérapeutique ni prescription en R11.

## RÈGLE NO-DROP — AUCUNE MESURE ABANDONNÉE

Autorités :
- `docs/CEPHALO_COM_VALUE_AUDIT.md`
- `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`

**Une mesure bloquée n'est jamais supprimée.** Elle devient une dette scientifique active avec raison du blocage + Next exact de récupération.

`BLOCKED != DROPPED`

Récupération déjà effectuée au closeout R11 :
- source primaire Tweed 1954 retrouvée pour FMA/IMPA ;
- IMPA historique `90±5°` confirmé par le texte primaire Tweed comme variation `85–95°` autour de 90° ;
- FMA primaire Tweed = repère 25°, variation 20–30° : ne pas lui attribuer silencieusement `26±4°` ;
- règle de compensation IMPA primaire retrouvée : chaque degré de FMA au-dessus de 25° décale l'IMPA cible d'un degré sous 90° ; exemple Tweed `FMA 35° → IMPA 80°` ;
- source primaire Downs 1948 identifiée pour l'inter-incisif ; attribution historique `131±3°` retrouvée mais valeur à relire directement dans le primaire avant activation ;
- `U1-FH 107±5°` corroboré dans littérature peer-reviewed mais filiation primaire exacte encore ouverte ;
- surplomb/recouvrement conservés, avec références populationnelles à versionner plutôt qu'une fausse norme universelle ;
- toutes les valeurs linéaires CRANIOM 9 ans/adulte restent en file de récupération si la preuve numérique primaire directe n'est pas encore acquise.

Aucune de ces dettes ne doit être effacée lors de R12/R13. La recherche de preuve se poursuit dès qu'elle est nécessaire pour activer la mesure/référence concernée.

## VALEURS BLOQUÉES MAIS CONSERVÉES

Les statuts suivants restent non activables tant que la preuve correspondante manque :
- `CONVENTIONAL_REFERENCE_ONLY`
- `HISTORICAL_ONLY_BLOCKED`
- `DIVERGENT_BLOCKED`
- `CONSTRUCTION_BLOCKED`

Ils désignent une dette scientifique, jamais un abandon.

McNamara reste inert/scale-blocked. Les références actuelles ne sont pas actives pour classification patient. Les références CRANIOM extrêmes restent descriptives/traçables, pas diagnostiques.

## FICHIERS CLÉS R11

- `backend/schemas/cephalo_evidence.py`
- `backend/services/cephalo_diagnostic_rule_registry.py`
- `backend/services/cephalo_r11_diagnostic_safety.py`
- `backend/tests/test_cephalo_diagnostic_rule_registry.py`
- `backend/tests/test_cephalo_r11_diagnostic_safety.py`
- `backend/tests/test_cephalo_r11_missing_data_contract.py`
- `docs/CEPHALO_COM_VALUE_AUDIT.md`
- `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`
- `docs/CEPHALO_DIAGNOSTIC_SPEC.md`

## NEXT EXACT — R12

R12 seulement, dans une nouvelle fenêtre.

Goal canonique R12 : **Problem list + objectifs**.

Succès minimum : chaque item de problem list et chaque objectif référence explicitement les findings/diagnostics validés dont il dérive ; aucune indication ou option thérapeutique R13 ne doit fuiter dans R12 ; données manquantes/contradictions restent visibles et fail-closed.

Avant modification :
1. lire `AGENTS.md` ;
2. lire `STATE.md` ;
3. lire `docs/CEPHALO_DIAGNOSTIC_SPEC.md` ;
4. lire `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md` ;
5. lire ce handover ;
6. vérifier master/HEAD/PR/CI réels ;
7. créer une branche R12 depuis master final vérifié.

## PROMPT EXACT À COLLER DANS LA NOUVELLE FENÊTRE R12

```text
MISSION — DIGITAL CROWN / CÉPHALOMÉTRIE — R12 PROBLEM LIST + OBJECTIFS

Tu reprends le chantier Céphalométrie de Digital Crown.

RÈGLE DE CONTINUITÉ
Cette fenêtre est exclusivement consacrée à R12.
Ne démarre pas R13 ici.
À la fermeture de R12, tu dois obligatoirement :
1. certifier le lot ;
2. merger si toutes les preuves sont acquises ;
3. vérifier master post-merge ;
4. mettre à jour le fichier canonique ;
5. créer un handover compact dans docs/handovers/ pour R13 ;
6. me fournir le prompt exact à coller dans une nouvelle fenêtre pour R13.

REPO
hraaaaf/Digital_crown

REPRISE OBLIGATOIRE
Lis dans cet ordre :
1. AGENTS.md
2. STATE.md
3. docs/CEPHALO_DIAGNOSTIC_SPEC.md
4. docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md
5. docs/handovers/2026-09-12-cephalo-r11-to-r12-handover.md
Puis vérifie repo/master/HEAD/PR/CI avant toute modification.

ÉTAT VÉRIFIÉ R11
- R11 implementation candidate : 6916dee975acb83d13acd540d5d2e4a8f839a478
- CI #3477 : SUCCESS
- T2 #2452 : SUCCESS
- PR #437 : merged
- merge implementation : bc66b58b6ee4459362d3bd52150877908bdc996c
- master post-merge implementation vérifié : bc66b58b6ee4459362d3bd52150877908bdc996c
- aucun déploiement

CONTRAT R11 À NE PAS CASSER
- measurement evidence → normative context optionnel → finding → diagnostic hypothesis → contradictions/missing data → clinician validation ultérieure
- landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan
- production diagnostic rule registry vide tant qu'une règle n'est pas source-lockée/revue
- unavailable evidence ne peut supporter/opposer un finding ou diagnostic
- inactive norm ne produit aucune classification patient et ne supporte/oppose aucun finding
- missing refs doivent être réellement manquantes/bloquées
- aucune prescription/indication/option thérapeutique dans R12

RÈGLE NO-DROP MESURES
- aucune mesure n'est abandonnée ;
- BLOCKED signifie dette scientifique active, jamais suppression ;
- si une preuve manque, la rechercher ; si une construction manque, la verrouiller ;
- ne jamais remplacer une preuve absente par une approximation silencieuse ;
- conserver chaque mesure et son état jusqu'à résolution ;
- lire et respecter docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md.

R12 — GOAL CANONIQUE
Problem list + objectifs.
Chaque item référence explicitement les findings/diagnostics validés dont il dérive.

SUCCESS R12
- schéma explicite et versionné pour problem-list items et objectifs ;
- provenance vers findings/diagnostics exacts ;
- contradiction/missing data propagées et visibles ;
- fail-closed si un item prétend dériver d'une preuve non disponible/non validée ;
- aucune transformation automatique d'une hypothèse non validée en problème confirmé ;
- aucune indication, contre-indication, option thérapeutique ou plan de traitement en R12 ;
- aucune mesure existante supprimée pour insuffisance de preuve : recherche/queue scientifique obligatoire ;
- goldens positif / négatif / missing / contradiction ;
- invariants inter-objets ;
- exact-head CI verte + T2 verte ;
- review/thread audit propre ;
- diff scope propre ;
- canonical mis à jour ;
- PR mergée ;
- master post-merge vérifié ;
- handover R13 écrit.

AUTONOMIE
Avance sans demander validation tant qu'aucun vrai human gate n'est rencontré. Corrige puis recertifie si CI rouge. Ne déploie pas sur Vercel sans autorisation explicite.

UI/UX
R12 n'est pas un lot visuel par défaut. Si tu modifies une UI : BEFORE → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports 390/768/1280+ → comparaison/tests → score visuel.

CLOSEOUT
Ne conclus pas tant que toute action connue et autorisée n'est pas exécutée : certification → merge → master post-merge → canonical → handover R13 → closeout final.

COMMUNICATION
Résultat → preuve → prochaine action.
À chaque message de travail, affiche les REPÈRES connus sans inventer de % ni de preuve.
```

## SÉQUENCE RESTANTE APRÈS R11

`R12 problem list/objectifs → R13 options thérapeutiques → R14 validation clinique → R15 studio UX/UI → R16 PDF → R17 certification/closeout`
