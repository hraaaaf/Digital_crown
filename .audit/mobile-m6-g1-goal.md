# M6-G1 — Goal visuel verrouillé

Base produit : `895ab9e7b03aecc60d721c46ba814f1b8770b57f`
BEFORE : run `32854639273`, artifact `9565703939`.

## Goal

Donner au mobile Digital Crown une identité visuelle plus propriétaire sans alourdir l'interface : motif clinique abstrait dans le fond + bottom navigation premium avec capsule active fluide.

## Défauts BEFORE mesurés

- fond G0 propre mais générique : halos + gradient uniquement ;
- aucune signature clinique/dentaire discrète ;
- aucun active pill dans la bottom navigation ;
- cible tactile minimale mesurée : **38,5 px** ;
- actif signalé seulement par couleur/point ;
- 0 overflow et 0 erreur runtime à préserver.

## Cible fond

- conserver le socle glass G0 ;
- ajouter un motif **100 % CSS**, sans asset ni requête réseau ;
- réseau nodal très léger : points + liaisons fines ;
- deux grandes courbes abstraites rappelant une arcade dentaire, jamais un pictogramme de dent ;
- opacité faible, priorité absolue à la donnée clinique ;
- plus présent sur Dashboard/Onboarding, atténué sur contextes cliniques ;
- aucun `background-attachment: fixed` ;
- high-contrast : motif supprimé ;
- reduced transparency / fallback G0 conservés.

## Cible bottom navigation

- conserver la barre glass flottante ;
- **cible tactile ≥48 px** pour chaque onglet ;
- capsule arrondie derrière l'icône active ;
- capsule partagée qui se déplace entre les onglets via Framer Motion `layoutId` ;
- mouvement court, amorti, sans bounce ni glow ;
- actif : icône + label renforcés ; inactifs : lisibles mais secondaires ;
- notification dot attaché à l'icône, pas au bouton entier ;
- `aria-current="page"` sur l'onglet actif ;
- `prefers-reduced-motion` : transition instantanée ;
- safe-area inférieure respectée ;
- aucune modification de route, permission, donnée ou logique métier.

## Succès observable

1. Un seul `[data-mobile-nav-active-pill]` est présent et se trouve dans l'onglet actif.
2. La position X du pill change réellement Agenda → Finance.
3. Tous les boutons bottom-nav mesurent ≥48 px de haut.
4. Le motif clinique est présent sur le shell via pseudo-élément CSS et reste discret.
5. High-contrast supprime le motif et conserve les surfaces opaques certifiées G0.
6. 0 overflow horizontal et 0 erreur runtime à 390 / 768.
7. Les vues Agenda et Finance restent fonctionnellement identiques hors navigation/skin.

## Preuve requise

- BEFORE Agenda + Finance : 390 / 768 ;
- mockup verrouillé avant code ;
- build frontend ;
- AFTER mêmes 4 vues + Onboarding 390 + Contexte RDV 390/768 ;
- probes pill / position / touch targets / motif / high-contrast ;
- inspection visuelle BEFORE → mockup → AFTER ;
- score visuel final seulement après inspection.

Aucun Vercel.
