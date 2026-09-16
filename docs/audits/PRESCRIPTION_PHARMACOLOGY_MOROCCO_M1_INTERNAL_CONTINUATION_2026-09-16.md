# Digital Crown — Pharmacologie & produits bucco-dentaires Maroc — Internal continuation

Date: 2026-09-16
Status: ACTIVE — internal/documentary only

## Goal
Construire un référentiel marocain complet de ce qu'un chirurgien-dentiste peut prescrire, recommander ou utiliser en prévention/soins bucco-dentaires : médicaments + OTC + parapharmacie + hygiène + prothèse + orthodontie + prévention, sans contact AMMPS et sans affaiblir les règles fail-closed.

## Success
1. Chaque médicament pertinent possède, selon disponibilité des preuves : DCI, spécialités/formes marocaines, dosage/concentration, indication dentaire, posologie adulte, posologie pédiatrique pondérale si applicable, âge/poids, durée, dose maximale, contre-indications, précautions, interactions et sources.
2. Chaque produit non-médicamenteux possède : catégorie, usage/indication, population, modalités d'utilisation, précautions/contre-indications lorsqu'elles existent, statut de preuve et exemples de formes disponibles au Maroc lorsque vérifiables.
3. Le référentiel couvre médicaments, OTC et parapharmacie bucco-dentaire; il ne se limite pas aux 7 familles Wave 1.
4. Les 7 familles Wave 1 restent explicitement non activées tant qu'aucun vrai RCP AMMPS conforme au contrat M1 n'est disponible pour toute donnée réglementaire qui l'exige.
5. Aucun état de preuve insuffisant n'est transformé en donnée clinique automatiquement exploitable.

## Scope obligatoire — médicaments
- antalgiques / antipyrétiques ;
- AINS ;
- antibiotiques et associations pertinentes en odontologie ;
- antifongiques ;
- antiviraux pertinents ;
- antiseptiques médicamenteux ;
- anesthésiques locaux et vasoconstricteurs associés ;
- corticoïdes ;
- traitements des lésions buccales / aphtes / mucites lorsque pertinents ;
- agents hémostatiques médicamenteux et produits d'urgence du cabinet ;
- médicaments de prise en charge des urgences médicales au cabinet dentaire ;
- tout autre médicament réellement pertinent pour la pratique dentaire au Maroc.

## Scope obligatoire — OTC / parapharmacie / hygiène / prévention
- dentifrices : fluorés, hypersensibilité, gingival/parodontal, enfant, orthodontie, anti-caries, autres indications prouvées ;
- bains de bouche / solutions de rinçage : antiseptiques, fluorés, gingivaux, post-opératoires, haleine, xérostomie, autres indications prouvées ;
- gels, sprays et solutions buccales non soumis à prescription ;
- brosses à dents manuelles et électriques, y compris spécifiques orthodontie/prothèse/enfant ;
- brossettes interdentaires ;
- fil dentaire, ruban dentaire, superfloss et porte-fil ;
- hydropulseurs / irrigateurs buccaux ;
- gratte-langue et accessoires d'hygiène linguale ;
- révélateurs de plaque ;
- substituts salivaires, gels/sprays de xérostomie ;
- produits fluorés d'usage à domicile et prévention carieuse ;
- vernis fluorés et autres agents préventifs professionnels lorsque pertinents ;
- produits de reminéralisation / gestion de sensibilité lorsque leur indication est documentée ;
- produits désensibilisants professionnels ou à domicile ;
- produits de blanchiment/éclaircissement supervisés ou recommandés par le dentiste, avec concentrations, indications, précautions et contre-indications lorsqu'ils relèvent du scope de soins ;
- chewing-gums / pastilles bucco-dentaires lorsque pertinents et documentés ;
- produits de contrôle de l'halitose ;
- hygiène orthodontique : cire orthodontique, brossettes, fils spécifiques, protections et accessoires ;
- hygiène des implants et parodontale : brosses mono-touffe, brossettes adaptées, fils spécifiques, autres accessoires pertinents ;
- hygiène de prothèse amovible : nettoyants, brosses à prothèse, comprimés/solutions de nettoyage ;
- adhésifs/fixatifs pour prothèses dentaires : crèmes, poudres, bandes/coussinets ;
- protections et soins des tissus sous prothèse lorsque médicalement pertinents ;
- produits d'hygiène pédiatrique selon âge ;
- produits post-chirurgicaux / post-extraction non médicamenteux lorsque pertinents ;
- dispositifs simples destinés à prévenir traumatismes/irritations buccales ;
- autres produits de parapharmacie spécifiquement recommandés en cabinet dentaire au Maroc.

## Hors scope par défaut
- cosmétique pur sans bénéfice bucco-dentaire démontré ;
- gadgets marketing sans indication ou utilité dentaire établie ;
- matériaux restaurateurs, instruments, équipements et dispositifs techniques de cabinet relevant d'un référentiel dispositif/matériovigilance distinct ;
- recommandations commerciales non fondées sur une source vérifiable.

## Décision propriétaire
Aucune demande, formulaire, email, appel ou autre contact AMMPS n'est autorisé. Toute réactivation exige une nouvelle autorisation explicite.

## État Wave 1
- paracetamol: fail-closed; identité AMMPS publique observée, aucun RCP cible capturé.
- ibuprofen: fail-closed; identité AMMPS publique observée, aucun RCP cible capturé.
- amoxicillin: fail-closed; présentations AMMPS exactes déjà identifiées, aucun RCP cible capturé.
- penicillin_v: fail-closed; identité AMMPS publique observée, aucun RCP cible capturé.
- metronidazole: fail-closed; présentations publiques observées, aucun RCP cible capturé.
- clarithromycin: fail-closed; présentations AMMPS observées, aucun RCP cible capturé.
- clindamycin: fail-closed; présentation systémique/orale courante utile non prouvée dans le pass actuel.

## Travail interne autorisé
- constituer l'inventaire exhaustif des classes, DCI et produits para réellement pertinents ;
- sourcer les données cliniques et d'usage avec au moins deux références sérieuses lorsque le risque le justifie ;
- distinguer preuve réglementaire marocaine, preuve clinique internationale et recommandation d'usage ;
- consolider les identités de présentation déjà prouvées et leurs références de provenance publique ;
- vérifier que les manifests/consommateurs ne transforment jamais un état pending en donnée clinique exploitable ;
- renforcer les tests négatifs du gate déterministe ;
- préparer la structure de données commune médicament/OTC/para sans prétendre à une validation non acquise.

## Interdits
- aucun contact AMMPS ;
- aucune URL RCP devinée ;
- aucun fallback étranger présenté comme preuve réglementaire marocaine ;
- aucune donnée clinique inventée ;
- aucune activation clinique sans validation correspondante.

## Next exact
Produire la taxonomie exhaustive médicaments + OTC + parapharmacie bucco-dentaire, puis établir la liste détaillée des entrées à documenter avant enrichissement posologique et validation croisée.
