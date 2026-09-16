# START PROMPT — DIGITAL CROWN / PATIENT COMPANION CONTINUATION

Repo: `hraaaaf/Digital_crown`

Chantier: Patient Companion / reste du Lot D puis roadmap compétitive.

## Première action obligatoire

Avant toute modification :

1. Lire intégralement depuis le **master ACTUEL** :
   - `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`
   - `docs/audits/PATIENT_COMPANION_D0.md`
   - `docs/audits/PATIENT_COMPANION_D1.md`
   - `docs/audits/PATIENT_COMPANION_D2.md`
   - `docs/audits/PATIENT_COMPANION_CONTINUATION_HANDOVER.md`
2. Vérifier ensuite sur GitHub :
   - SHA actuel de `master` ;
   - présence des merges D0/D1/D2 dans l'historique ;
   - PR ouvertes pertinentes ;
   - CI/certifications actuelles ;
   - éventuelle divergence depuis le handover.
3. Ne jamais supposer qu'un SHA indiqué ici est encore actuel.

## Vérité canonique au départ

D0 = CLOSED.
D1 = CLOSED.
D2 = CLOSED.

D2 :
- PR #523 MERGED ;
- certified PR head `206f58e6571c6fdfa2af8e726ce032d694928799` ;
- merge commit `6cc0c41fd64d40ef8929bebe11c67ecc4fc42672` ;
- post-merge CI #4574 / run `35100604875` SUCCESS ;
- post-merge PostgreSQL #917 / run `35100604888` SUCCESS.

Il **n'existe pas de D3 canonique** au moment du closeout D2.

La roadmap utilise encore le placeholder `D1+ — useful patient workflows beyond the minimum shell` pour la suite Patient Companion. Ne pas inventer un D3 sans d'abord borner le scope et réviser explicitement la roadmap si ce nom est retenu.

## Goal de cette nouvelle conversation

Déterminer et exécuter le prochain lot Patient Companion réellement utile, à partir de l'état produit actuel, sans duplication ni affaiblissement des frontières D0/D1/D2.

## Ordre d'exécution attendu

1. Audit read-only du Patient Companion patient-facing actuel et des contrats backend réellement disponibles.
2. Identifier les vrais gaps restants par rapport au produit souhaité, sans recopier :
   - Patient Journey interne ;
   - D2 staff administration ;
   - Agenda ;
   - Documents ;
   - Media Core ;
   - notification/push/preferences existants.
3. Proposer un lot borné : Goal / Success / Proof / exclusions / risques.
4. Choisir le chemin le plus simple et sûr ; si une décision produit majeure reste réellement équivalente, présenter A/B avec recommandation.
5. Si scope validable sans human gate, continuer automatiquement : implémentation → tests → preuve.
6. Pour toute UI : BEFORE 390×844 / 768×1024 / 1280×900 → Goal/référence → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.
7. Vérifier non-régression DB / patients / documents / fonctions existantes proportionnellement au risque.
8. PR propre, diff exact, reviews/threads/mergeability, CI exact-head.
9. Merge seulement après le gate propriétaire requis par le chantier.
10. Post-merge : vérifier comportement/CI puis closeout canonique.
11. Continuer au lot suivant tant qu'une action connue, autorisée et immédiatement exécutable reste.

## Hard boundaries

- aucun second modèle/source Patient, Appointment, Document ou Media ;
- aucun JWT cabinet côté patient ;
- aucun fallback public/non scopé pour documents/médias ;
- aucun secret d'invitation persisté en clair ;
- pas de mutation rendez-vous patient sans nouveau contrat explicitement conçu/certifié ;
- pas de délégation employé implicite ;
- pas de remote gateway implicite ;
- pas de migration destructive ;
- aucune DB cabinet réelle touchée pendant développement/certification ;
- aucun déploiement Vercel sans autorisation explicite.

## Reste de la roadmap après Patient Companion

- Lot E — Connect Hub ;
- Lot F — Ortho Journey ;
- Lot G — Assurance Maroc ;
- Lot H — Lab / Prosthesis Collaboration ;
- Lot I — BI / Recall / Outcomes.

Si aucun nouveau workflow Patient Companion n'est retenu, passer à Lot E uniquement après audit anti-duplication des infrastructures notification/push/preferences existantes.

## Format de reprise

À chaque message de travail : Résultat → preuve → prochaine action.

Fin de message :

📍 REPÈRES
- chantier/lot
- Goal
- repo/branche/PR/HEAD
- CI/run + état
- dernière preuve
- blocage réel
- Next exact
- Séquence restante
- avancement global si réellement connu
- effort suivant

Ne jamais déclarer un lot CLOSED sans preuve exacte.
