# HANDOVER — DIGITAL CROWN / CÉPHALOMÉTRIE — R17 FINAL

**Date :** 2026-09-14  
**Repo :** `hraaaaf/Digital_crown`  
**Canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Branche produit :** `codex/cephalo-r17-authoritative-pdf`  
**PR produit :** #481 — MERGED  
**Candidate HEAD certifié :** `58dcd4bfa2901f36e3d9b30e97629c87db89f80b`  
**Merge master produit :** `f0aafd9278791becdc6980e3804022231553cfd7`  
**Branche closeout docs :** `docs/cephalo-r17-closeout-v2`  
**PR closeout docs :** #485

## GOAL R17

Clôturer la restitution PDF céphalométrique de manière autoritaire et fail-closed : pour un même état clinique, API/UI/PDF doivent préserver le même sens scientifique et clinique essentiel, sans source de vérité parallèle dans le renderer.

## SUCCÈS OBSERVABLE — PRODUIT ATTEINT

Sur le candidate HEAD exact `58dcd4bfa2901f36e3d9b30e97629c87db89f80b` :

- CI #3931 : SUCCESS ;
- T2 Runtime Browser Certification #2850 : SUCCESS ;
- Cabinet Upgrade PostgreSQL Certification #365 : SUCCESS ;
- Clinic P3 Document Provenance Certification #37 : SUCCESS ;
- Settings TemplateEngine Reachability Certification #462 : SUCCESS ;
- Settings R11 TemplateBuilder Dependency Audit #622 : SUCCESS ;
- Settings R11 TemplateBuilder Reachability Audit #187 : SUCCESS ;
- M6-I Biometric Passkey Certification #1650 : SKIPPED, comportement normal pour ce scope ;
- reviews : 0 ;
- review threads : 0 ;
- PR #481 mergeable avant merge ;
- merge produit réel : `f0aafd9278791becdc6980e3804022231553cfd7` ;
- `master` post-merge vérifié exactement sur ce SHA ;
- aucun déploiement Vercel.

## BEFORE — DIVERGENCES PROUVÉES

Audit lecture seule R16/R17 :

- la route PDF injectait des champs client `ai_diagnostic` et `clinical_data` dans `analysis_data` avant génération ;
- l'ancien template HTML pouvait reconstruire des valeurs ou choix de présentation legacy, notamment technique Damon et logique interceptive liée à l'âge/denture ;
- l'ancien fallback ReportLab lisait des narratifs legacy ;
- le PDF n'était donc pas garanti comme simple projection du graphe typé et du Studio clinique R15.

Aucune capture visuelle humaine BEFORE n'a été produite dans cet environnement. La preuve BEFORE est code-level et contractuelle.

## ARCHITECTURE AFTER

### Projection unique

`backend/services/cephalo_pdf_projection.py`

- contrat `CEPHALO_PDF_PROJECTION_V1` ;
- construit une projection renderer-neutral depuis le typed runtime/read path et le snapshot Clinical Scientific Studio R15 ;
- valide la chaîne typée avant exposition des mesures ;
- conserve disponibilité, méthode/version, unité, calibration, source scientifique, provenance, blockers, missing data, contradictions et contre-indications ;
- ignore les champs legacy client comme source d'autorité clinique ;
- `document_state=COMPLETE` uniquement si validation clinique disponible et zéro blocker ; sinon `INCOMPLETE` ;
- en cas d'échec du typed projection read-path, `active_runtime_chain_verified=False`, mesures non promues et blocker explicite.

### DocumentFactory

`backend/services/document_factory.py`

- construit la projection avant filtrage legacy ;
- transmet cette projection au générateur ;
- les champs legacy peuvent rester dans les schémas HTTP pour compatibilité, mais ne déterminent plus l'autorité du PDF.

### Renderers

`backend/services/generators/bilan_ortho_gen.py`

- HTML et ReportLab consomment le même document model ;
- absence de projection → fail-closed ;
- suppression du chemin actif des inférences renderer-side Damon/interceptif/narratif ;
- correction du fallback ReportLab réel ;
- escaping des chaînes dynamiques HTML/ReportLab.

`backend/templates/bilan_ortho_authoritative.html`

- document incomplet explicitement signalé ;
- `EVALUABLE` n'est jamais assimilé à sélection ;
- `BLOCKED` n'est jamais assimilé à `DROPPED` ;
- R14 final exige une preuve praticien autoritaire.

## MATRICE DE CERTIFICATION R17

Couverte par les tests R17 :

- AVAILABLE ;
- NOT_COMPUTABLE ;
- missing data ;
- contradiction ;
- contre-indication ;
- provenance ;
- R13 EVALUABLE ≠ sélectionné ;
- R13 BLOCKED ≠ DROPPED ;
- R14 awaiting ;
- gate COMPLETE seulement avec `clinical_validation_available=True` et zéro blocker ;
- injections `ai_diagnostic` / `clinical_data` ignorées comme autorité ;
- aucun défaut Damon par défaut ;
- aucune inférence interceptive liée à l'âge ;
- aucune synthèse clinique fabriquée ;
- parité sémantique HTML/ReportLab ;
- état incomplet explicite ;
- escaping HTML/ReportLab ;
- PDF ReportLab réel, lisible par PyMuPDF, format A4, pages non blanches et blocs dans les limites.

## CORRECTIONS CI R17

Les échecs rencontrés ont été diagnostiqués puis corrigés, sans masquer les défauts :

1. compatibilité `short_label` legacy ;
2. bug réel fallback ReportLab `self.base_template` ;
3. oracle de test trop strict sur le mot anglais `INCOMPLETE` dans le HTML français ;
4. oracle de test sur apostrophe Jinja auto-échappée : assertion normalisée par `html.unescape`, sans désactiver l'escaping.

Le dernier état produit exact-head est CI #3931 SUCCESS.

## LIMITES EXPLICITES

- Le Studio R15 courant ne dispose pas encore d'un snapshot R14 autoritaire persisté exposé comme validation disponible ; le rendu réel courant doit donc rester `INCOMPLETE` / `AWAITING_CLINICIAN` tant que cette preuve n'existe pas.
- Le gate COMPLETE est contractuellement testé avec `clinical_validation_available=True` et zéro blocker, sans inventer un statut R14 non produit par le service courant.
- Un vrai PDF ReportLab est certifié par PyMuPDF. La parité HTML est testée au niveau template/contexte partagé ; WeasyPrint n'est pas une dépendance runtime actuelle, donc aucun faux certificat « deux PDF réels » n'est revendiqué.
- Pas d'inspection visuelle humaine finale du PDF dans cet environnement. Aucun score visuel humain n'est donc attribué.

## SCOPE FINAL PRODUIT

PR #481, candidate HEAD `58dcd4bfa2901f36e3d9b30e97629c87db89f80b` : 7 fichiers produit/tests, aucun frontend, aucun déploiement.

## CLOSEOUT R17

Le **produit R17 est fermé et mergé** sur `master` au SHA `f0aafd9278791becdc6980e3804022231553cfd7`.

Le closeout documentaire final est porté par `docs/cephalo-r17-closeout-v2` / PR #485, après abandon de la PR #484 devenue obsolète à la suite de l'avancement de `master`. Cette version du handover constitue la clôture documentaire dès que la PR #485 est mergée et que cette version est vérifiée sur `master`.

## Y A-T-IL UN R18 ?

**Pas de R18 fonctionnel planifié dans la roadmap céphalométrique actuelle.** La séquence canonique planifiée se termine à R17.

Cependant, le protocole `1 fenêtre = 1 R` impose qu'une nouvelle fenêtre de reprise prenne le numéro suivant et qu'un prompt de reprise existe. Donc **R18 existe uniquement comme fenêtre procédurale de post-closeout/reprise**, pas comme feature inventée.

## PROMPT COMPLET DE REPRISE R18

Tu es dans une nouvelle fenêtre de conversation : **R18 — post-closeout céphalométrie / reprise contrôlée**.

Règles :

1. Lire `AGENTS.md`, puis `STATE.md`, puis `docs/CEPHALO_DIAGNOSTIC_SPEC.md`, puis `docs/handovers/2026-09-14-cephalo-r17-final-handover.md`.
2. Vérifier avant toute modification :
   - repo `hraaaaf/Digital_crown` ;
   - `master` courant ;
   - PR produit #481 = MERGED ;
   - candidate R17 `58dcd4bfa2901f36e3d9b30e97629c87db89f80b` ;
   - merge produit `f0aafd9278791becdc6980e3804022231553cfd7` ;
   - PR closeout docs #485 = MERGED ;
   - closeout documentaire R17 présent sur `master` ;
   - CI/post-merge disponibles.
3. Ne pas rouvrir R17 en l'absence de régression prouvée.
4. Préserver les invariants : typed evidence autoritaire, fail-closed, `NOT_COMPUTABLE` reste indisponible, `EVALUABLE != selected`, `BLOCKED != DROPPED`, R14 final uniquement avec preuve praticien autoritaire, aucun contenu clinique fabriqué par le PDF.
5. **Aucune nouvelle feature R18 n'est pré-autorisée ni définie par le canonique actuel.** Après vérification post-closeout, identifier le prochain chantier uniquement depuis une source canonique existante ou une instruction explicite de l'utilisateur. Ne pas inventer une « R18 fonctionnelle » pour remplir la numérotation.
6. Si aucun nouveau chantier céphalométrique n'est défini, considérer la chaîne R0→R17 closeout comme terminée et ne modifier aucun code.
7. Aucun déploiement Vercel sans autorisation explicite.

**Goal R18 procédural :** vérifier que le closeout R17 est bien présent sur master et reprendre uniquement sur un prochain chantier réellement défini.  
**Succès :** master/PR/CI/docs concordants, aucun drift, et prochain chantier soit explicitement identifié, soit déclaré absent.  
**Preuve :** SHAs/PR/runs/docs exacts vérifiés au début de la fenêtre.

## NEXT EXACT

1. Merger la PR closeout docs #485 après CI verte.
2. Vérifier `master` post-merge documentaire et la présence de cette version du canonique/handover.
3. Dans une future fenêtre seulement, utiliser le prompt R18 ci-dessus.

## DÉPLOIEMENT

Aucun déploiement Vercel effectué ni autorisé.
