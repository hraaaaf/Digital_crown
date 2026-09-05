# Digital Crown — Mobile Canonical Navigation — Goal UI

Status: AWAITING VISUAL VALIDATION
Lot: MOB-4
Branch: `ux/mobile-canonical-navigation-mob4`
Baseline master: `e49907c20c1062e9691fb34c030bcc182289b760`

## Goal

Remplacer la navigation mobile actuelle orientée modules par une navigation **cockpit** centrée sur les usages fréquents, sans casser les deep links ni supprimer les vues existantes.

## Succès observable

1. maximum 5 entrées permanentes ;
2. `Aujourd’hui` ouvre la vue agenda ;
3. `Patients` ouvre directement la vue patients ;
4. le bouton central `+` ouvre le Quick Action Hub MOB-3 ;
5. `Assistant` ouvre Crown Bot ;
6. `Plus` regroupe les destinations secondaires autorisées ;
7. Finance / Labo / Sécurité restent accessibles via `Plus` selon rôle ;
8. anciens deep links `?tab=finance|lab|securite|bot|agenda` restent fonctionnels ;
9. aucun onglet non autorisé n’est exposé ;
10. aucune couleur ou police de marque n’est figée localement ;
11. aucun overflow horizontal sur 390 / 430 / 768 ;
12. interaction à une main sur 390×844.

## BEFORE — VERIFIED

Run `33945615036` ✅

- HEAD : `6e1c5ffe3314b7621ae22202091e978025f18a23`
- artifact : `9963244367`
- digest : `sha256:6c2416c3454270a0dcfe863c1b834fbea75d658437cc060c46741d8013cfb35d`
- viewports : `390×844`, `430×932`, `768×1024`
- mode : harness démo déterministe, aucune donnée cabinet.

Navigation réellement observée :

`Agenda / Finance / Envois Labo / Assistant / Sécurité`

Le type `Tab` contient déjà `patients`, mais cette vue n’est pas exposée dans la bottom nav.

## Navigation cible

1. **Aujourd’hui** → `agenda`
2. **Patients** → `patients`
3. **+** → Quick Action Hub existant
4. **Assistant** → `bot`
5. **Plus** → menu secondaire filtré par rôle

### Plus

Contenu possible selon rôle/capabilities :
- Finance
- Envois Labo
- Sécurité
- Équipe praticiens
- SuperAdmin si applicable

Aucune destination ne doit apparaître si non autorisée.

## Décisions d’architecture

- conserver `Tab` et les vues existantes ;
- ne pas supprimer les routes historiques ;
- `resolveDashboardTab()` continue d’accepter les anciens `tab=` ;
- le `+` central réutilise le Quick Action Hub MOB-3, aucun second moteur d’actions ;
- `Patients` devient une entrée permanente ;
- les modules secondaires passent dans `Plus`, pas hors du produit ;
- thèmes / surfaces / typographie restent issus des tokens Réglages cabinet.

## Hors scope MOB-4

- suppression des vues Finance / Labo / Sécurité ;
- refonte métier de ces modules ;
- changement des permissions backend ;
- modification des deep links desktop ;
- Vercel.

## Gate

1. BEFORE réel ✅
2. Goal UI ✅
3. mockup sur BEFORE réel ⏳
4. validation visuelle humaine ⏳
5. aucun code produit avant gate 4.
