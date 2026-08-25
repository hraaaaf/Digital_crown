# M4-D — RDV contextuel — Goal verrouillé

Date : 2026-08-25
Baseline canonique : `fa03efb858a27b3cd10e53346486d189ae785b47`
Produit byte-identique audité : `8a11a452cc7a3b14964a1908a32589700a4cb6f7`
BEFORE : run `32839944720` — SUCCESS
Artifact : `9560131369` — `sha256:f93c08316fb15fd1e42768f9ab81bc54f18ea9ad7f3b8f5d04e042aa3b0106a6`

## Goal

Depuis n’importe quelle vue Agenda qui affiche un rendez-vous existant, ouvrir **ce rendez-vous exact**, puis permettre de l’ouvrir sur le mobile appairé via le bridge opaque déjà certifié, sans exposer l’ID du rendez-vous, l’ID patient ni une donnée clinique dans le QR ou l’URL mobile.

## Défauts BEFORE vérifiés

1. **Jour : OK** — le clic sur `BENNANI Sara / Contrôle implant 36 / 10:30` ouvre `Modifier le Rendez-vous` avec le RDV exact.
2. **Semaine : OK** — même comportement exact.
3. **Mois : KO** — cliquer le RDV exact ouvre `Nouveau Rendez-vous`; la sélection du RDV est perdue.
4. **Bridge RDV absent** — aucune action `Ouvrir sur mobile` dans le RDV existant.
5. **Mobile : KO** — un contexte `appointment` aboutit à `Contexte indisponible` sur 390 / 430 / 768 px.
6. **Runtime : propre** — 0 erreur et 0 overflow horizontal sur les 7 captures BEFORE.

## Succès observable

### A. Sélection exacte Agenda

- Jour → clic RDV existant → `Modifier le Rendez-vous` exact.
- Semaine → clic RDV existant → `Modifier le Rendez-vous` exact.
- Mois → clic sur la puce RDV existante → `Modifier le Rendez-vous` exact, **jamais** `Nouveau Rendez-vous`.
- Clic sur le reste d’une case Mois vide → conserve le comportement `Nouveau Rendez-vous`.

### B. Bridge desktop → mobile

Sur un RDV existant, une action explicite `Ouvrir sur mobile` :

- cible uniquement un utilisateur du même cabinet avec permission `agenda` ;
- génère le même protocole opaque temporaire que Patient / Panoramique / Document ;
- QR = secret temporaire uniquement ;
- aucun `appointment_id`, `patient_id`, nom patient, motif ou horaire dans le QR / URL mobile ;
- destination finale : `/mobile/context`, sans ID ni query clinique ;
- contexte lié au cabinet, utilisateur et appareil ;
- permission et existence du RDV revalidées au moment de l’ouverture.

### C. Contexte mobile RDV

Sur 390 / 430 / 768 px, le contexte exact affiche sans ambiguïté :

- `Rendez-vous` ;
- patient ou libellé externe canonique ;
- date + heure/plage ;
- durée ;
- motif ;
- statut ;
- action de retour claire vers le mobile/agenda.

Aucun identifiant interne ne doit apparaître dans l’URL.

### D. Fail-closed

- RDV supprimé → indisponible ;
- permission `agenda` révoquée → refus ;
- mauvais cabinet / mauvais utilisateur / mauvais appareil → refus ;
- contexte expiré ou introuvable → état d’erreur explicite ;
- aucune fuite de ressource par fallback.

### E. UX/UI M4-D

- identité visuelle Agenda / Digital Crown conservée ;
- le CTA mobile est secondaire par rapport à `Enregistrer`, mais immédiatement compréhensible ;
- la puce RDV Mois devient une vraie cible interactive et tactile ;
- tous les **nouveaux contrôles M4-D** et la cible RDV Mois sont ≥44 px ;
- 0 overflow horizontal ;
- 0 erreur runtime ;
- le bridge n’introduit aucun redesign parasite du formulaire Agenda.

> Dette observée, hors scope de ce lot : plusieurs contrôles historiques de `AgendaModal` restent sous 44 px. M4-D ne prétendra pas les avoir corrigés sauf modification explicite de ces contrôles.

## Preuve requise

1. tests backend du protocole Appointment exact ;
2. tests frontend sélection Mois + contexte Appointment + absence d’ID/query ;
3. AFTER sur les mêmes états/viewports que le BEFORE, plus modal QR RDV ;
4. comparaison visuelle BEFORE → mockup → AFTER ;
5. CI exact-head + régressions Patient / Panoramique / Document ;
6. score visuel M4-D attribué après inspection réelle.
