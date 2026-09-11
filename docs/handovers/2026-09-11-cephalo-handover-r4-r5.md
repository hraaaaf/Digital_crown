# Handover Céphalométrie — R4 → R5

Date: 2026-09-11
Repo: `hraaaaf/Digital_crown`

## Goal
Continuer le chantier Céphalométrie sans perte de contexte, fermer proprement R4 CRANIOM, puis poursuivre R5 Steiner avec une chaîne scientifique typée, traçable, fail-closed, ZERO LLM, sans normes/diagnostic tant que les sources et contrats ne sont pas prouvés.

## Règle scientifique obligatoire
Pour toute donnée scientifique, définition géométrique, norme, seuil, interprétation ou recommandation clinique :
- croiser au minimum **2 sources sérieuses**, primaires si possible ;
- ajouter une **3e source** en cas de divergence, ambiguïté historique ou enjeu élevé ;
- ne jamais coder une convention clinique à partir d'une seule source secondaire ;
- distinguer explicitement : **fait vérifié / convention versionnée / hypothèse / blocage** ;
- une mesure n'entre dans le runtime que si sa **définition géométrique, unité, landmarks et provenance** sont concordants ;
- en cas de nomenclature divergente, versionner la géométrie exacte au lieu d'utiliser un nom générique ambigu.

## Contraintes projet
- Déploiement local/on-premise.
- ZERO LLM.
- Aucun déploiement Vercel sans autorisation explicite.
- Pas de CI entre micro-étapes si du travail indépendant reste : préparer le lot, puis certification CI/T2 finale avant merge.
- Ne jamais déclarer un lot fermé sans preuve exact-head.

# État R4 — CRANIOM

## Fermé/mergé avant ce handover
- R1 calibration/provenance
- R2 chaîne scientifique active
- R3 conventions géométriques
- R4 U1 / Frankfort
- R4 L1 / Downs

### R4 L1 / Downs closeout
- PR #412 : merged
- merge SHA : `3aab122ee0f5c845ada7b80079845336805bd80d`
- master post-closeout : `c6ed747b9b67c725d88b6cb5cc85914d969e2aed`
- closeout : `docs/handovers/2026-09-11-cephalo-r4-l1-downs-closeout.md`

## R4 Inter-incisif — PR #413
- branche : `feat/cephalo-r4-interincisal`
- PR : #413
- base : `master` @ `c6ed747b9b67c725d88b6cb5cc85914d969e2aed`
- HEAD vérifié : `3ce931d624cd520e2addc5db434eeb5806138141`
- état PR au dernier check : open, draft, non mergée
- changed files : 15
- commits : 23
- CI #3296 / run `34618235047` : **SUCCESS**
- T2 #2291 / run `34618235088` : **SUCCESS**
- le dernier stale contract connu a été corrigé avant ces runs verts

### Contrat R4 Inter-incisif
- `CRANIOM_INTERINCISAL_ANGLE_V1`
- `CRANIOM_U1_L1_INTERINCISAL_V1`
- `CRANIOM_INTERINCISAL_DEG_V1`
- axes dentaires : U1 apex→incisal et L1 apex→incisal
- parité stricte avec runtime `Inter_Incisif`
- aucune calibration requise
- fail-closed : landmarks manquants / axes dégénérés / cross-image
- aucune norme, aucun diagnostic, aucun traitement

### Audit résiduel R4
Ne pas forcer l'implémentation si le gate scientifique/données n'est pas levé :
- overjet / overbite : variables CRANIOM prouvées, mais frame de projection CRANIOM exacte insuffisamment prouvée par les sources actuellement établies → `BLOCKED_SOURCE_FRAME`
- Stomion : variable pertinente mais landmark absent → `BLOCKED_LANDMARK`
- A″B″ : dépend d'un protocole NHP / regard horizontal non disponible → `BLOCKED_PROTOCOL`
- forme mandibulaire Ar.Gs / Gi.Me : Gi/Gs absents → `BLOCKED_LANDMARK`
- SN / plan mandibulaire CRANIOM : construction exacte insuffisamment verrouillée → `BLOCKED_SOURCE_GEOMETRY`

### Next R4 exact
1. Re-vérifier PR #413 au HEAD `3ce931d...`.
2. Vérifier mergeability/reviews/threads.
3. Puisqu'CI + T2 exact-head sont déjà verts, si aucun nouveau problème n'apparaît : ready → squash merge avec expected head → vérifier master.
4. Créer `docs/handovers/2026-09-11-cephalo-r4-interincisal-closeout.md`.
5. Mettre l'inventaire R4 à jour et considérer R4 fermé avec les blocs résiduels explicitement documentés.

# État R5 — Steiner

## Branche active
- branche : `feat/cephalo-r5-steiner-skeletal`
- HEAD branche au dernier check : `1b5f62ae31bc74045a34a87c4c9bb998ada8e4ef`
- aucun PR R5 ouvert volontairement à ce stade
- branche stackée sur le travail R4 préparatoire ; elle devra être réancrée/rebasée proprement sur master après fermeture R4 avant certification finale R5

## Déjà présent sur R5
### Géométrie Steiner versionnée
`backend/services/cephalo_steiner_geometry.py`
- `steiner_sna_deg_v1`
- `steiner_snb_deg_v1`
- `steiner_anb_deg_v1`
- `steiner_u1_na_deg_v1`
- `steiner_l1_nb_deg_v1`
- `steiner_u1_na_mm_v1`
- `steiner_l1_nb_mm_v1`

### Typed evidence Steiner squelettique
`backend/services/cephalo_steiner_evidence_adapter.py`
- SNA
- SNB
- ANB
- analyse_id = `STEINER`
- namespaces Steiner séparés
- IDs historiques CRANIOM préservés
- pas de norme / classification / diagnostic / traitement

### Runtime evidence composition
`backend/services/cephalo_runtime_evidence.py`
- compose CRANIOM + Steiner
- conserve les namespaces CRANIOM historiques
- ajoute Steiner de façon additive
- valide le graph global via `EvidenceGraphSnapshot`

## Provenance Steiner
Référence bibliographique à utiliser pour le papier 1953 :
- Steiner CC, *Cephalometrics for you and me*, Am J Orthod. 1953
- DOI correcte : `10.1016/0002-9416(53)90082-7`

La chaîne R5 doit conserver cette référence correcte. Ne pas réintroduire une DOI proche mais erronée.

## État dentaire Steiner
Définitions préparées mais intégration globale encore à terminer et certifier :
- U1-NA°
- U1-NA mm
- L1-NB°
- L1-NB mm

Contraintes :
- angles : pas de calibration
- distances : calibration physique obligatoire et provenance valide
- distances = distance perpendiculaire du bord incisif à NA/NB selon la convention documentée
- ne pas typer tant que le croisement scientifique ≥2 sources n'est pas consigné dans le code/doc de preuve

## R5 restant connu
- tests runtime filtrés par `analysis_id` pour éviter les compteurs globaux fragiles
- intégrer U1-NA° / U1-NA mm / L1-NB° / L1-NB mm dans l'evidence graph
- vérifier parité avec le runtime ou ajouter le runtime clinique unique s'il n'existe pas encore
- S-line : ne pas confondre avec Ricketts E-line ; point/protocole Steiner exact à sourcer et vérifier avant code
- SN-MP / SN-OP : sourcer la construction exacte avant activation
- aucune norme Steiner active à ce stade

# Roadmap restante
- R5 Steiner
- R6 Tweed/Merrifield
- R7 Wits/Jacobson + Downs
- R8 McNamara
- R9 Ricketts + tissus mous
- R10 registre normatif
- R11 diagnostic multiaxial
- R12 problem list + objectifs
- R13 options thérapeutiques
- R14 validation clinique
- R15 studio clinique UX/UI
- R16 PDF/restitution
- R17 certification/closeout

# Next exact pour la nouvelle conversation
1. Lire ce fichier.
2. Vérifier repo / master / PR #413 / HEADs exacts avant toute écriture.
3. Fermer R4 Inter-incisif si PR #413 reste propre et exact-head vert.
4. Réancrer `feat/cephalo-r5-steiner-skeletal` sur master post-R4.
5. Reprendre R5 avec la règle scientifique ≥2 sources fiables pour chaque mesure.
6. Finaliser le dentaire Steiner par bloc cohérent.
7. Lancer CI/T2 seulement quand le lot R5 est réellement prêt pour certification.

# Preuves à ne pas perdre
- PR #413 exact-head `3ce931d624cd520e2addc5db434eeb5806138141`
- CI #3296 : SUCCESS
- T2 #2291 : SUCCESS
- R5 branch HEAD `1b5f62ae31bc74045a34a87c4c9bb998ada8e4ef`
- ZERO LLM
- aucun Vercel
