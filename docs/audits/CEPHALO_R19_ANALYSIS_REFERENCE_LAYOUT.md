# CEPHALO R19 — ANALYSIS REFERENCE LAYOUT

## Goal

Recomposer l'étape Céphalométrie selon le mockup validé par le cabinet, **uniquement pour l'agencement et le niveau de détail** : téléradio/tracé à gauche, sélecteur d'analyse, tableau de mesures à droite, détail explicatif de la mesure sélectionnée et liaison visuelle mesure ↔ construction.

Le thème du mockup n'est PAS une source de design. Digital Crown conserve ses tokens `getCephaloPalette()`, sa typographie, ses couleurs, ses composants et ses états.

## Référence visuelle verrouillée

- Source : mockup fourni et explicitement validé par le cabinet le 2026-09-14.
- Dimensions source : `1495 × 1052`.
- SHA-256 source : `ae44a5052cc8feb8805f885bc1c56c74d1a5f4c6378d02c557012da3643cf060`.
- Usage autorisé : structure de page, hiérarchie, densité et détail du panneau d'analyse.
- Usage interdit : copier le thème, inventer une norme, inventer une mesure ou changer une convention scientifique pour ressembler au mockup.

## BEFORE

Le BEFORE produit reste la preuve R18 certifiée. Référence BEFORE visuelle : R18 Tracing AFTER #7, run `34889128064`, 15/15 états valides sur `390×844`, `768×1024`, `1280×900`, zéro overflow horizontal, score HFE R18 enregistré `9.4/10`.

## Contrat R19 livré

1. Analyses séparées : `Tous | Steiner | Tweed | McNamara | COM | Ricketts`.
2. `COM` n'est plus un alias de McNamara.
3. Desktop large : panneau d'analyse voisin de la téléradio ; viewports plus petits : empilement responsive sans overflow.
4. Chaque ligne du tableau sélectionnée/survolée focalise sa construction géométrique sur la téléradio.
5. Aucune donnée inventée : valeur absente = `NC`, norme absente = `—`.
6. L'écart UI n'est calculé que si la valeur et `norm_mean` existent dans le payload.
7. Les constructions COM réutilisent les conventions céphalométriques déjà versionnées ; aucun changement de formule backend R19.
8. McNamara et Ricketts conservent leurs contrats R18.
9. La base historique R18 reste immuable.
10. La fuite historique McNamara dans COM est neutralisée sans supprimer les landmarks nécessaires aux constructions COM R19.

## Preuves exact-head avant merge

HEAD candidat final : `97ae1f236e73119b977f976e70732b42ee4ae86c`.

- CI #4166, run `34904860533` — **SUCCESS** ; frontend tests + build **SUCCESS** ; full backend regression DB / patients / documents **SUCCESS**.
- Cephalo R19 Analysis Reference AFTER #9, run `34904860852` — **SUCCESS**.
- Artefact AFTER #9 : `10372492103`, digest `sha256:0985faf00396105d080f8da787bcee8d661e8ad4a6e0a12c10a1bfbddf247c49`.
- T2 Runtime Browser #3070 — **SUCCESS**.
- Cabinet Upgrade PostgreSQL #585 — **SUCCESS**.
- Cephalo R15 AFTER #96 — **SUCCESS**.
- Cephalo R15bis AFTER #57 — **SUCCESS**.
- Cephalo R1 AFTER #66 — **SUCCESS**.
- M6-I #1870 — `SKIPPED` attendu.

Contrat visuel certifié : 3 viewports × 6 modes = **18/18 états valides**, zéro overflow horizontal, zéro erreur page/console ; COM = 10 lignes, 15 constructions ; fuite McNamara en COM = 0.

## Comparaison visuelle avec le mockup

- `1280×900` : téléradio/tracé à gauche, panneau à droite, sélecteur, tableau `Mesure / Valeur / Norme / Écart` et détail de mesure conformes à la hiérarchie cible.
- `768×1024` : panneau empilé, lisible sans débordement.
- `390×844` : interface compacte, valeurs lisibles, aucun overflow horizontal.
- thème : tokens Digital Crown conservés ; thème du mockup non copié.

**Score visuel R19 : 9.4/10.**

## Merge et closeout

PR #496 : **MERGED** par squash.

Merge produit réel : `d62171871eca6d5c428cef22044fe874ff2dda00`.

Le merge a été effectué sur le `master` réel `279a8b56c77dfca36a8e1316d1a5f87d6aa2308e`, dont la dérive depuis le précédent master concernait uniquement Prescription Intelligence et ne touchait aucun fichier céphalométrique R19. Après merge, `master` a été vérifié sur `d62171871eca6d5c428cef22044fe874ff2dda00` avant ce commit documentaire de closeout.

Aucun déploiement Vercel.

## État

`R19 — FERMÉ ET MERGÉ.`
