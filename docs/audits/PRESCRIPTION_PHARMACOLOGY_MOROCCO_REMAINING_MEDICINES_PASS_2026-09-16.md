# Digital Crown — Pharmacologie dentaire Maroc — Remaining medicines pass

Date: 2026-09-16
Status: RESEARCH ONLY — NOT FOR CLINICAL ACTIVATION

## Goal
Documenter les familles restantes après antalgiques/anti-infectieux/urgences/anesthésiques : corticoïdes buccaux, hémostase, xérostomie et sédation, en séparant preuve clinique, disponibilité Maroc et statut d'activation.

## Corticoïdes / muqueuse buccale

### Hydrocortisone buccale
- Usage clinique documenté : soulagement des ulcères buccaux inflammatoires non infectieux.
- Référence pratique NHS : hydrocortisone buccale jusqu'à 4 applications/comprimés buccaux par jour, jusqu'à 5 jours selon la présentation décrite; enfants <12 ans uniquement sur prescription médicale.
- SDCEP : pour une ulcération buccale, envisager un corticoïde topique; un corticoïde systémique n'est évoqué que si ulcération sévère, avec recours spécialisé approprié.
- Ne pas utiliser sur lésion traumatique/infectieuse supposée sans diagnostic; ulcère inexpliqué persistant >=3 semaines = filière d'évaluation urgente, pas traitement symptomatique seul.
- Maroc : disponibilité exacte de la forme buccale non prouvée dans ce pass -> `TO_VERIFY_MA`.
- Activation : `TO_VALIDATE`; aucune substitution automatique par une autre forme de corticoïde.

Sources :
- https://www.acutedentalproblems.sdcep.org.uk/guidance/management-of-oral-conditions/common-oral-conditions/oral-ulceration/
- https://www.nhs.uk/medicines/hydrocortisone-buccal-tablets/about-hydrocortisone-buccal-tablets/
- https://www.nhs.uk/medicines/hydrocortisone-buccal-tablets/who-can-and-cannot-use-hydrocortisone-buccal-tablets/

### Triamcinolone / dexamethasone / prednisolone topiques ou bains
- Pertinence clinique potentielle en médecine buccale, mais aucune posologie ne doit être promue depuis l'inventaire seul.
- Statut : `SPECIALIST_OR_EXCEPTION` / `TO_VALIDATE` jusqu'à preuve formulation + posologie + disponibilité Maroc.

## Hémostase

### Acide tranexamique
- SDCEP 2026 : le bain de bouche d'acide tranexamique peut réduire le saignement comparé au placebo chez certains patients sous antithrombotiques, mais le bénéfice supplémentaire face aux mesures locales n'est pas clairement établi.
- SDCEP n'en recommande pas la prescription de routine par le praticien dentaire de premier recours; si prescrit par le médecin du patient, il peut être utilisé en complément des mesures locales.
- Maroc : recherche publique ciblée de ce pass non concluante -> `TO_VERIFY_MA`.
- Activation dentaire autonome : `SPECIALIST_OR_EXCEPTION`.

Sources :
- https://companion.sdcep.org.uk/management-of-dental-patients-taking-anticoagulants-or-antiplatelet-drugs/managing-bleeding-risk/haemostatic-measures/
- https://www.sdcep.org.uk/media/4gslzda1/sdcep-management-of-dental-patients-taking-anticoagulants-or-antiplatelet-drugs-2nd-edition.pdf

## Xérostomie

### Pilocarpine
- Indications documentées : symptômes de sécheresse buccale liés à l'hypofonction salivaire après radiothérapie tête/cou; sécheresse buccale du syndrome de Sjögren.
- Dose adulte fréquemment référencée : 5 mg trois fois par jour dans la synthèse ADA; le SmPC Salagen 5 mg confirme la formulation et les indications, avec schémas propres selon indication.
- Contre-indications majeures concordantes : asthme non contrôlé, hypersensibilité, situations où le myosis est indésirable; le SmPC ajoute maladie cardiorénale cliniquement significative non contrôlée et autres situations à risque cholinergique.
- Précautions : maladie cardiovasculaire significative, asthme contrôlé/BPCO, risque de déshydratation par sudation, effets cholinergiques.
- Pédiatrie : aucune donnée ne doit être activée depuis cette passe; `NOT_ROUTINE_PEDIATRIC`.
- Maroc : disponibilité exacte non prouvée dans ce pass -> `TO_VERIFY_MA`.
- Activation : `SPECIALIST_OR_EXCEPTION` jusqu'à validation Maroc et rôle prescripteur.

Sources :
- https://www.ada.org/resources/ada-library/oral-health-topics/xerostomia
- https://www.medicines.org.uk/emc/product/1370/smpc
- https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=438cfaa3-b5f6-4d75-ac22-b0b4e07bb118

### Cevimeline
- ADA la cite comme sialogogue oral pour xérostomie, mais disponibilité/autorisation Maroc non prouvée.
- Statut : `SPECIALIST_OR_EXCEPTION`, `TO_VERIFY_MA`, aucune activation.

### Substituts salivaires / gomme sans sucre
- À traiter dans le dataset para, séparément des sialogogues systémiques.

## Sédation / anxiolyse

### Protoxyde d'azote + oxygène
- AAPD : méthode reconnue d'analgésie/anxiolyse en dentisterie pédiatrique lorsque le praticien, l'équipement, la sélection du patient et le monitoring sont appropriés.
- Si >50% de N2O ou association avec d'autres sédatifs, la probabilité de sédation modérée/profonde augmente et les exigences correspondantes doivent être appliquées.
- Contre-indications/limitations pédiatriques citées par AAPD : certaines BPCO, troubles émotionnels sévères/dépendances, premier trimestre de grossesse, déficit MTHFR, obstruction nasale/rhume compromettant la voie d'administration.
- Maroc : disponibilité et cadre réglementaire dentaire exact non prouvés dans ce pass -> `TO_VERIFY_MA`.
- Activation : `SPECIALIST_OR_EXCEPTION`; jamais comme simple prescription.

Sources :
- https://www.aapd.org/research/oral-health-policies--recommendations/use-of-nitrous-oxide-for-pediatric-dental-patients/
- https://www.aapd.org/research/oral-health-policies--recommendations/monitoring-and-management-of-pediatric-patients-before-during-and-after-sedation-for-diagnostic-and-therapeutic-procedures/

### Midazolam
- AMMPS RMMG 2026 : MIDAZOLAM MYLAN 5 mg/mL solution injectable (IM/IV/rectale), boîtes de flacons 1 mL et 10 mL, est référencé dans le répertoire générique marocain.
- Une ancienne présentation MIDAZOLAM AGUETTANT 5 mg/5 mL apparaît dans la liste des médicaments retirés; cela ne remet pas en cause l'existence d'autres présentations actuelles.
- SmPC actuel : midazolam est indiqué pour sédation consciente avec ou sans anesthésie locale avant/pendant procédures diagnostiques ou thérapeutiques. Administration lente et titrée obligatoire; doses réduites chez sujets >=60 ans, fragiles ou chroniquement malades.
- Exemples SmPC, non activés dans Digital Crown : adulte <60 ans IV initial 2–2,5 mg avec titration; pédiatrie 6 mois–5 ans initial 0,05–0,1 mg/kg IV, 6–12 ans 0,025–0,05 mg/kg IV. <6 mois : sédation consciente non recommandée dans ce SmPC. Ces valeurs sont conservées comme preuve de référence, pas comme protocole dentaire marocain.
- Activation : `SPECIALIST_OR_EXCEPTION`; nécessite protocole de sédation, monitoring, compétences, équipement de secours et validation réglementaire locale.

Sources :
- https://ammps.gov.ma/repertoire-medicaments-generiques?page=11
- https://www.ammps.gov.ma/basesdedonnes/medicaments-retires?page=40
- https://www.medicines.org.uk/emc/product/13192/smpc
- https://www.aapd.org/research/oral-health-policies--recommendations/monitoring-and-management-of-pediatric-patients-before-during-and-after-sedation-for-diagnostic-and-therapeutic-procedures/

### Diazepam
- AMMPS : VALIUM 5 mg et 10 mg comprimés et solution buvable sont listés comme commercialisés dans la base publique observée.
- Disponibilité ≠ indication dentaire. Statut : `SPECIALIST_OR_EXCEPTION`; posologie dentaire non activée dans ce pass.

Source Maroc :
- https://www.ammps.gov.ma/recherche-medicaments?page=758

### Hydroxyzine
- Une ancienne forme injectable ATARAX 100 mg est observée comme retirée du marché; aucune conclusion sur l'ensemble des formes actuelles ne peut être tirée de cette seule observation.
- Statut : `TO_VERIFY_MA`, `SPECIALIST_OR_EXCEPTION`.

Source :
- https://www.ammps.gov.ma/basesdedonnes/medicaments-retires?page=6

## Guardrails
- Ces données sont une passe de recherche, pas un moteur de prescription.
- `Commercialisé` ou présence RMMG ne signifie pas indication dentaire.
- Aucune dose de sédation n'est activable sans protocole séparé, monitoring, compétence et cadre réglementaire.
- Les produits non prouvés au Maroc restent `TO_VERIFY_MA`.
- Les formes systémiques à risque ou à usage spécialisé restent `SPECIALIST_OR_EXCEPTION`.

## Next exact
1. Réconcilier ces lignes avec le CSV maître.
2. Vérifier les omissions médicaments : AINS restants, antifongiques/antiviraux, traitements de muqueuse, hémostatiques locaux, urgence/sédation.
3. Passer ensuite au dataset para complet avec usage, âge/population, mode d'emploi, précautions et preuve Maroc.
