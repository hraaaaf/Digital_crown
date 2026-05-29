# UX/UI Context

This file is the canonical UX/UI context entrypoint for DigitalCrown.

Use it after `process/context/all-context.md` when the task needs design systems, styling modifications, or Framer Motion adjustments.

---

## Scope

This group covers:

- "Ghost Elite" Glassmorphism layout design rules and theme configurations.
- Tailwind CSS v4 variables and custom styles in `frontend/src/index.css`.
- Framer Motion animation configurations, transitions, and gesture behaviors.
- Assistance Docking (`EliteDock`) and Header centralized modules.
- Form controls, inputs, and medical readability scaling.

It does not cover:

- Backend endpoint routing or database structure (that belongs in `database/` context).
- AI panoramic landmark coordinate formats (that belongs in `ia-vision/` context).

## Read When

Read this entrypoint when:

- creating or updating frontend UI elements, layouts, pages, or components
- adjusting CSS stylesheets or theme configurations
- optimizing user flow, drag-and-drop actions, or modal display layers
- correcting styling or layout errors (e.g. z-index blocking clicks)

## Quick Routing

- use `frontend/src/index.css` for primary/secondary Tailwind v4 custom tokens
- use `frontend/src/components/EliteDock.tsx` for global intelligent assistant widgets
- use `frontend/src/features/` for feature-specific layouts and cards

## Source Paths

- `process/context/uxui/all-uxui.md`

## Update Triggers

Update this group when:

- Design tokens, color palettes, or primary assets are updated
- Layout structure guidelines (like centralizingHeader or Docking rules) are updated
- Tailwind v4 configuration in CSS is restructured
