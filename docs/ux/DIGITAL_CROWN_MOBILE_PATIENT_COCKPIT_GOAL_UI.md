# Digital Crown — Mobile Patient Cockpit — Goal UI v1

Status: DRAFT — mockup pending visual validation
Canonical parent: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-product-canonical`
Lot: MOB-1
Deployment: none

## Goal

Concevoir l'écran mobile patient canonique de Digital Crown comme un cockpit clinique opérationnel, utilisable à une main et permettant au praticien d'identifier un patient, voir l'information critique et lancer l'action utile en moins de 30 secondes.

Le résultat ne doit pas être une réduction du dossier patient desktop.

## Scénario primaire

1. Le praticien ouvre `Patients` depuis la navigation mobile.
2. La recherche est immédiatement disponible.
3. Il saisit quelques lettres du nom, prénom ou numéro de dossier.
4. Il sélectionne le patient.
5. Le cockpit affiche immédiatement : identité, alerte médicale, prochain RDV, contexte financier autorisé et actions natives.
6. Il peut appeler, ouvrir WhatsApp, prendre une photo clinique, scanner un document ou encaisser selon permission sans traverser le dossier desktop.

## Invariants fonctionnels du mockup

Le Goal UI doit montrer au minimum :

- header Digital Crown mobile cohérent avec la PWA existante ;
- recherche patient très visible et immédiatement accessible ;
- identité patient : nom/prénom, numéro dossier, âge, assurance si disponible ;
- alerte médicale critique clairement prioritaire ;
- boutons Appeler et WhatsApp ;
- prochain rendez-vous / prochaine séance ;
- finance synthétique seulement si permission ;
- actions rapides Photo clinique, Scanner document et Encaisser si permission ;
- accès au contexte patient mobile existant sans exposer les studios lourds desktop ;
- état de synchronisation discret ;
- navigation mobile canonique exploratoire : `Aujourd'hui / Patients / + / Assistant / Plus`.

## Hiérarchie cible

Ordre visuel recommandé :

1. identité / recherche ;
2. alerte médicale ;
3. actions de contact ;
4. prochain RDV ;
5. finance synthétique ;
6. actions rapides ;
7. navigation principale.

L'alerte médicale doit être perceptible avant la finance et avant les actions secondaires.

## Direction visuelle

Conserver le langage Digital Crown mobile existant :

- fond médical perle / très clair ;
- surfaces premium légèrement vitrées ;
- cartes fortement arrondies ;
- ombres faibles et propres ;
- bleu Digital Crown comme couleur primaire ;
- accent vert uniquement pour actions positives / WhatsApp ;
- rouge réservé aux alertes médicales et risques ;
- typographie dense mais lisible, hiérarchie forte ;
- iconographie simple type Lucide ;
- aucune table desktop ;
- aucun graphe ;
- aucun empilement de six onglets ;
- aucun décor gratuit qui ralentit la lecture clinique.

## Ergonomie

- usage principal à une main ;
- touch targets >= 48 px sur les actions majeures ;
- bottom navigation compatible safe-area ;
- CTA principaux atteignables dans la moitié basse ;
- recherche et alerte visibles sans scroll sur un viewport 390 px si possible ;
- pas d'overflow horizontal ;
- le contenu clinique reste compréhensible à 200 % de zoom texte autant que possible ;
- les états offline / loading / empty / error devront être dérivés après validation du screen principal.

## Viewports de référence

- 390 px : primaire ;
- 430 px : large phone ;
- 768 px : tablette compacte / boundary du routage actuel.

Le premier mockup doit représenter le viewport 390 px. Les déclinaisons 430/768 viennent après validation de la direction visuelle.

## Hors scope du Goal UI

Ne pas intégrer dans ce cockpit :

- odontogramme complet ;
- ClinicalHub complet ;
- Master Plan ;
- RVG Studio ;
- Panoramic Studio complet ;
- Céphalométrie ;
- Document Studio complet ;
- Analytics ;
- Treasury Hub ;
- paramètres cabinet ;
- administration Marketplace.

Ces workflows restent desktop sauf décision ultérieure explicitement motivée.

## Critères de validation du mockup

Le mockup est accepté uniquement si :

- la priorité patient est évidente en moins de 3 secondes ;
- l'alerte médicale ne peut pas être confondue avec une information secondaire ;
- Appeler / WhatsApp / Photo / Scan / Encaisser sont immédiatement compréhensibles ;
- l'écran reste calme malgré la densité fonctionnelle ;
- il ressemble à Digital Crown mobile et non à une application générique ;
- aucune fonction desktop lourde n'est artificiellement miniaturisée ;
- la navigation à cinq entrées reste lisible ;
- la direction est suffisamment précise pour servir de Goal UI avant implémentation.

## BEFORE

La baseline fonctionnelle actuelle est vérifiée dans le canonique parent et dans le code mobile existant. La capture visuelle BEFORE du viewport 390 px doit être produite et archivée avant toute implémentation MOB-2. Le présent lot MOB-1 peut produire le Goal UI et son mockup sans déclarer l'implémentation commencée.

## Next exact

Produire le mockup haute fidélité 390 px du Patient Cockpit selon les invariants ci-dessus, puis le soumettre à comparaison/validation visuelle avant tout code produit.
