# LOT05 / J10H — Rapport panoramique : qualité rédactionnelle et lisibilité PDF (sans image)

**22 octobre 2026 · Recherche uniquement · PR DRAFT empilée sur #1017 · Aucun patient utilisé.**

## Décision produit

La **radiographie reste accessible uniquement depuis Imagerie**. Le PDF est un document écrit autonome, lisible, destiné à porter des **observations documentées par le dentiste** et une synthèse. Le PDF ne comporte **aucune photographie, aucun cliché, schéma FDI, téléradiographie, QR image ou annexe céphalométrique**. Il ne doit pas faire naître par défaut une conclusion normale, un diagnostic, un traitement ou un acte.

Références publiques examinées séparément des exigences Digital Crown :

- [RadRap — Orthopantomogramme / panoramique dentaire](https://www.radrap.ch/comptesrendus/orthopantomogramme-panoramique-dentaire) : modèle rédactionnel avec *indication, technique, résultat, conclusion* ; exemples de domaines dentaires incluant FDI, maxillaire/mandibule, parodonte, dents de sagesse, sinus, ATM. **Les exemples de normalité de RadRap ne doivent pas être repris si le praticien n'a pas explicitement vérifié cette normalité.**
- [Schnitzer et al. 2026, *Frontiers in Dental Medicine*, 7:1769864](https://www.frontiersin.org/journals/dental-medicine/articles/10.3389/fdmed.2026.1769864/full), 5 mars 2026 : étude exploratoire monocentrique sur **50 panoramiques** et comptes rendus structurés, démontrant une amélioration de la lisibilité/complétude par rapport aux rapports narratifs, avec limites de comparabilité (comptes rendus structurés par une seule dentiste, deux évaluateurs, absence d'aveugle).
- L'ontologie interne déjà en place dans `backend/services/panoramic_report_engine.py` est plus sûre que la reprise littérale de ces exemples externes : intitulés déterministes, conclusions uniquement sur annotations explicites, zones non évaluées identifiées.

## Problèmes techniques corrigés

1. **Perte silencieuse de texte** : la méthode ancienne `_categorize_findings` n'ajoutait que les listes `- ` sous des titres `### `. Des paragraphes rédigés par le praticien, questions et conclusions pouvaient disparaître, et les lignes hors section étaient perdues. Le parseur pur `backend/services/panoramic_pdf_outline.py` préserve chaque ligne substantielle, y compris texte libre, et classe les rubriques sans inventer de contenu médical.
2. **Présentation peu clinique** : l'ancienne maquette affichait les observations en petites cartes en 2 colonnes avec beaucoup de marges, gênant la lecture du raisonnement radiologique. Le template est désormais **A4 une colonne**, entête léger, données patient, **Indication/Question clinique**, **Technique/Qualité**, **Observations par domaine**, **Réponse**, **Conclusion/Synthèse**, pied de page discret et identité du praticien. Les rubriques n'apparaissent que si les sources les contiennent. FDI conservés sans autonumérotation inventée.
3. **Risque d'injection HTML dans le rendu** : Jinja2 autoescape activé pour les champs nom/médecin et observations libres. Les chaînes `<img>`, `<svg>` et `<script>` de test apparaissent comme texte, jamais comme ressources chargées. Le moteur PDF ne lit pas de fichier image patient.
4. **Cohérence pages longues** : gestion des sauts A4 et des titres pour les rapports longs, numérotation des pages sans image.

## Non objectifs

- Aucune modification du générateur d'observations `panoramic_report_engine.py` ou de son ontologie, aucun diagnostic ou contenu médical nouveau, ni nom/role considéré « signature numérique ».
- Aucune connexion patient par la nouvelle preuve : WeasyPrint génère uniquement des PDF fictifs localement. Pas de nouveau endpoint ni base de données, pas de poids IA, pas de suppression ou changement de stockage radio.
- Aucune autorisation implicite d'usage commercial du modèle FDI : CC BY-NC-SA toujours bloquante. Dossiers patients / clinique V1.5 NO-GO.
- Les PR #1006 #1012 #1013 #1017 restent DRAFT et sans fusion.

## Critères de certification technique

Run exact HEAD du workflow `.github/workflows/lot05-j10h-panoramic-pdf-quality.yml` : conserver les **5 tests J10G** (zéro image, endpoint RBAC intact), ajouter **7 tests J10H** (respect du texte, paragraphes hors listes, absence de normalité inférée, long rapport multipage, vraies mesures de PDF, aucune image sur chacune des pages, sécurité autoescape) ; valider extraction de tous les constats FDI et de la synthèse. Ajouter examen visuel du rendu synthétique si possible, mais ne pas le confondre avec une revue clinique. Aucun merge/déploiement avant feu vert indépendant.

## Structure cible

**COMPTE RENDU RADIOGRAPHIQUE — PANORAMIQUE DENTAIRE** ; patient, date, référence du dossier, praticien associé à la fin ; *Question clinique (si saisie), Technique/qualité, Observations radiographiques documentées (classées par domaines), Réponse à la question (si rédigée), Synthèse des seules constatations validées.* À la fin : absence de garantie de normalité des zones non étudiées, absence de diagnostic ou traitement automatique, confidentialité.

**Règle de régression permanente : PDF 100 % texte.**
