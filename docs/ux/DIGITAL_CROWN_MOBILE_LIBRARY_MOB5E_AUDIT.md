# Digital Crown Mobile — MOB-5E Bibliothèque clinique — Audit

Status: **AUDIT LOCKED / BEFORE UI**

## Baseline

- Repository: `hraaaaf/Digital_crown`
- Baseline `master`: `9cb740bc52efc9bf734c19fefc3c4f07470eba80`
- Source lot: MOB-5D merge #360
- Branch: `ux/mobile-library-mob5e`
- No Vercel deployment.

## Goal

Bring the existing clinical library to the mobile cockpit as a **fast consultation surface**, not a raw desktop port.

## Verified desktop source of truth

Desktop routes already exist and are real:

- `/bibliotheque`
- `/bibliotheque/:code`
- `/science-hub`

Desktop component:

- `frontend/src/features/clinical-ref/EliteLibrary.tsx`

Clinical source of truth:

- `frontend/src/data/clinical-protocols/index.ts`
- 50 protocols assembled from versioned JSON files under `frontend/src/data/clinical-protocols/`
- no backend API or second datastore is used for these protocols

Protocol contract:

- `act_code`
- `category`
- `act_names[]`
- `difficulty`
- `duration_min`
- `checklist[]`
- `steps[]`
- `pitfalls[]`
- `drugs[]`
- `patient_instructions[]`

Desktop-local preferences:

- favorites: `localStorage['dc_favs']`
- recents: `localStorage['dc_recents']`

## Verified desktop capabilities

`EliteLibrary` currently provides:

- search by act name / code / category
- categories + counts
- favorites
- recents
- alpha / difficulty / category sorting
- grid / list presentation
- protocol detail route
- keyboard command palette
- protocol navigation
- print shortcut
- clinical content tabs
- separate soin mode

`ClinicalRefContent` exposes:

- checklist
- steps
- pitfalls / risks
- drugs
- patient instructions

## Mobile BEFORE

On baseline `9cb740b…`:

- canonical bottom nav remains 5 entries
- `Plus` contains Notifications, Stock, Équipe, Frontdesk, Finance, Labo, Sécurité according to role
- no Bibliothèque entry exists
- no `library` mobile dashboard tab exists
- no dedicated mobile clinical-library view exists

Therefore the current mobile user cannot reach the clinical library from the mobile cockpit.

## MOB-5E mobile scope locked

### Include

- `Plus → Bibliothèque`
- mobile dashboard route `?tab=library`
- same `CLINICAL_PROTOCOLS` source as desktop
- 50-protocol search
- compact protocol cards: name, category, duration, difficulty
- fast protocol opening
- simplified mobile reading of the existing clinical sections
- favorites reuse only if it remains zero-duplication and uses the existing `dc_favs` key
- role access limited to clinical roles already allowed to use practitioner tools: `DENTISTE`, `ADMIN`
- preview/demo uses fixture presentation only and never cabinet data

### Exclude from mobile V1

- Science Hub: desktop only
- desktop category rail
- keyboard command palette
- print workflow
- grid/list switch
- desktop sort controls
- raw desktop side panel port
- new clinical API / backend datastore
- duplicated protocol JSON
- new medical content or altered drug/dose text
- new soin-mode behavior unless existing component can be reused without UX regression

## Data / security conclusion

The library content is static/versioned application data, not tenant clinical records. MOB-5E must not create an API or database table merely to make mobile work.

Patient/cabinet data must not be introduced into this lot.

## Validation required

UI/UX certification is mandatory:

1. exact BEFORE on baseline `9cb740bc52efc9bf734c19fefc3c4f07470eba80`
2. written Goal + mockup/reference
3. implementation
4. exact AFTER on same viewports:
   - 390×844
   - 430×932
   - 768×1024
5. assertions:
   - canonical nav = 5
   - no horizontal overflow
   - no page/console runtime errors
   - Bibliothèque reachable only via Plus
   - search returns protocol from shared source
   - protocol detail renders existing source content
6. targeted tests + production build
7. visual comparison + score

## Success criterion

A dentist can find and open an existing protocol on mobile in a few seconds, with no duplicated clinical source and no Science Hub mobile scope creep.
