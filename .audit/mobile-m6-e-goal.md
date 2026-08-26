# M6-E — Communication patient mobile — Goal

## BEFORE
- Source: M4-A exact-head artifact `9587628216`, run `32914297032`, product HEAD `23c402bbac770f6dd1deacaf88c48bdb3f1710ea`.
- Master post-closeout `c5db61a352f908cef8a15db72b6a7d7116b73bac` ne modifie que la documentation depuis ce produit.
- 390 / 430 / 768 inspectés: aucun overflow, aucune erreur runtime; `Appeler` = 54 px; pas d'action WhatsApp.

## Goal
Permettre depuis le contexte Patient mobile de contacter le patient en un geste par appel ou WhatsApp, sans inventer l'indicatif d'un numéro ambigu, sans préremplir de donnée patient/clinique dans WhatsApp et sans dégrader Agenda / Photo clinique / Scan.

## Succès observable
1. `Appeler` reste disponible avec un `tel:` sûr et une cible >=48 px.
2. `WhatsApp` utilise uniquement `https://wa.me/<numéro international digits-only>` lorsque le numéro est explicitement international (`+...` ou `00...`).
3. Un numéro local/ambigu ne déclenche jamais un chat potentiellement vers le mauvais destinataire: état désactivé + explication courte `Indicatif international requis`.
4. Aucun nom patient, motif, note clinique, montant ou texte prérempli n'est ajouté à l'URL WhatsApp.
5. `Agenda`, `Photo clinique` et `Scanner un document` restent fonctionnels et visuellement hiérarchisés.
6. Actions rapides compactes sur 390 / 430 / 768, aucune cible <48 px, zéro overflow, zéro erreur runtime.
7. États testés: téléphone international, téléphone local ambigu, téléphone absent.

## Références techniques
- `tel:` conforme au schéma RFC 3966; préférence au format global quand disponible.
- Les ancres HTML peuvent utiliser `tel:`; comportement dépend du device.
- WhatsApp Click to Chat: URL `wa.me` avec numéro international; aucune donnée préremplie dans ce lot.

## Cible visuelle
- Trois actions rapides compactes dans une grille 3 colonnes: `Appeler`, `WhatsApp`, `Agenda`.
- Chaque carte >=64 px de haut; icône au-dessus du libellé pour préserver la lisibilité à 390 px.
- `Agenda` conserve le rôle CTA primaire bleu.
- `Appeler` et `WhatsApp` restent secondaires, cohérents avec le système visuel existant; pas de grand bloc vert de marque.
- Si WhatsApp est indisponible, sa carte reste visible mais atténuée; microcopy courte sous la grille.
