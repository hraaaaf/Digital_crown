# R4-B — Modèles documentaires premium — Audit + Goal visuel

Date : 2026-08-19
Repo : `hraaaaf/Digital_crown`
Périmètre : **Réglages → Design & Ambiance → Modèles d'ordonnance / typographie documentaire**.
Hors scope : Document Studio clinique, contenu médical, archivage, QR (R5).

## Goal

Conserver les cinq familles de modèles persistées (`swiss`, `royal`, `clinical`, `modern`, `heritage`) mais les transformer en cinq identités documentaires réellement distinctes, sobres, médicales et premium, sans sacrifier la lisibilité ni la stabilité A5 mono-page.

## Succès

1. Les cinq modèles sont reconnaissables visuellement à faible zoom sans lire leur nom.
2. L'arabe FR/AR est rendu avec de vrais glyphes, jamais avec des carrés de fallback.
3. Aucun choix typographique dans Réglages ne promet une police absente du moteur PDF.
4. Le corps médical reste volontairement cohérent entre modèles : patient/date, médicament, forme, dosage, posologie restent immédiatement lisibles.
5. Chaque modèle tient sur une page avec le scénario d'audit commun.
6. Aucun clipping, collision, glyph missing ou régression du contenu.
7. BEFORE / wireframes / AFTER comparables sur les cinq modèles.

## Preuve BEFORE

Workflow : `Settings Document Models Visual Audit`.
Run de référence complet avec logo : #3, run `32203590581`.
Artifact : `settings-document-models-audit`, id `9348355380`, head `4ea5889da36bd24dd69585043d6278fa55e22f70`.
Scenario identique pour les cinq modèles : même patient, même date, même logo, même identité FR/AR, mêmes trois prescriptions, mêmes couleurs.

## Audit visuel BEFORE

### Verdict global

- Concept des cinq familles : **9.4/10 — GARDER**.
- Exécution visuelle actuelle : **6.9/10 — REFONTE CIBLÉE**.
- Lisibilité du corps médical : **8.7/10 — GARDER**.
- Différenciation entre modèles : **5.8/10 — TROP FAIBLE**.
- Vérité typographique : **4.0/10 — À CORRIGER**.
- Bilingue FR/AR actuel : **3.0/10 — DÉFAUT BLOQUANT** (glyphes arabes en carrés sur les cinq rendus d'audit).

### Scores par modèle

| Modèle | Score BEFORE | Verdict | Force principale | Faiblesse principale |
|---|---:|---|---|---|
| Swiss Clinic | 7.0/10 | RETOUCHER | grille claire, asymétrie médicale crédible | header chargé, identité encore générique |
| Royal Elite | 7.3/10 | RETOUCHER | composition centrée/logo forte | ne paraît pas réellement plus premium/classique |
| Clinical Grid | 7.8/10 | GARDER / AFFINER | meilleur système de grille, plus distinctif | corps/header encore trop proche des autres |
| Modern Flush | 7.4/10 | GARDER / AFFINER | respiration et asymétrie intéressantes | ressemble trop à Swiss avec un trait différent |
| L'Héritage | 6.5/10 | REFONDRE | double filet et centre donnent une base | aucun vrai caractère patrimonial/serif aujourd'hui |

## Dette typographique vérifiée

`backend/static/assets/fonts/` contient actuellement uniquement :
- `Outfit-Regular.ttf`
- `Outfit-Bold.ttf`

Pourtant `BaseTemplate` tente aussi d'enregistrer Amiri, Montserrat, InterTight et Playfair. Les choix frontend annoncent en plus JetBrains Mono et Lora. Conséquences :
- arabe : fallback sans glyphes → carrés noirs ;
- `Inter Tight` : n'est pas réellement disponible côté PDF ;
- `Playfair Display` : n'est pas réellement disponible côté PDF ;
- `JetBrains Mono` / `Lora` : ne disposent pas de mapping PDF dédié ;
- seul Outfit est réellement embarqué aujourd'hui.

R4-B doit donc corriger la vérité typographique, pas seulement redessiner des traits.

## Wireframes premium retenus

### 1. Swiss Clinic — précision suisse

```text
[LOGO]  DR / CABINET                         الهوية العربية
        spécialité FR                       التخصص
        ───────── accent court

                 ORDONNANCE

PATIENT                                             DATE
---------------------------------------------------------
corps prescription — grille médicale commune
```

Principes : asymétrie maîtrisée, alignements stricts, aucune décoration gratuite.

### 2. Royal Elite — symétrie premium

```text
                    [LOGO]
          DR / CABINET   |   الهوية العربية
                 spécialité
        ───────────────────────────

                 ORDONNANCE
```

Principes : axe central fort, logo plus petit qu'actuellement, détails fins, beaucoup d'air. Pas d'effet “menu de mariage”.

### 3. Clinical Grid — rigueur clinique

```text
[LOGO] | DR / CABINET          | الهوية العربية
       | spécialité            | التخصص
=======|=======================|================

                 ORDONNANCE
```

Principes : grille explicite, séparation technique subtile, meilleure lecture institutionnelle.

### 4. Modern Flush — contemporain

```text
[LOGO]
DR / CABINET                         الهوية العربية
spécialité                           التخصص
████ accent rail court

        ORDONNANCE
```

Principes : composition décentrée, masses typographiques fortes, une seule signature graphique.

### 5. L'Héritage — papeterie classique

```text
                    [LOGO]
              DR / CABINET
              spécialité FR
              الهوية العربية
           ─────────────────
           ─────────────────

                 ORDONNANCE
```

Principes : serif réellement disponible ou nom générique honnête, filets très fins, calme et solennité. Zéro faux luxe.

## Doctrine commune

À GARDER pour les cinq :
- format A5 ;
- patient/date ;
- alignement médicament / forme / dosage ;
- posologie sous la ligne médicament ;
- footer discret ;
- compression mono-page existante.

À CHANGER :
- typographie absente/trompeuse ;
- arabe cassé ;
- headers trop similaires ;
- noms premium non soutenus par l'exécution.

À NE PAS FAIRE :
- cinq corps de prescription différents ;
- décorations lourdes ;
- multiplication de modèles ;
- couleurs “luxe” forcées ;
- dépendance réseau pour les polices.

Statut : **AUDIT + GOAL + WIREFRAMES VERROUILLÉS — AVANT IMPLÉMENTATION**.
