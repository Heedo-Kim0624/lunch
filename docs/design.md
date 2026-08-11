# Design — Lunch Machine

## Experience Goal

The first screen should communicate within two seconds: pull once, receive one lunch decision. Account screens should feel like another printed ticket from the same machine, not a separate dashboard.

## Interaction Hierarchy

1. Optional setup: machine paper label `조건 고르기`
2. Primary: `점심 추천 레버 당기기`
3. After a ticket appears: `이걸 먹을래요`
4. Secondary: `다른 메뉴 뽑기`

Only one primary action is emphasized in each state. Loading, success, and error states are announced through a polite live region.

## Visual Direction

- A compact retro lunch-ticket machine rather than a generic dashboard.
- Warm paper, ink, enamel, and metal tokens instead of product-library defaults.
- Ticket typography carries the result; surrounding copy remains quiet.
- Motion reinforces the lever and ticket output but never blocks input.

## Accessibility Contract

- Every interaction uses a native button with an action-oriented visible label.
- Focus styles remain visible on all machine controls.
- Pointer target size is at least 44 by 44 CSS pixels.
- Status changes use `aria-live` and do not rely on color alone.
- Reduced-motion users receive state changes without lever or ticket travel animation.
- The filter dialog uses native checkboxes, traps keyboard focus, closes with Escape or the backdrop, and returns focus to its trigger.
- Filter copy explains same-row OR, cross-row AND, and the unrestricted empty state before users apply selections.

## Design-system Check

Astryx XDS `Button` documentation was inspected. It requires accessible labels, recommends one primary action per view, action-specific copy, and loading feedback. The package examples are React-based, while this project is Nuxt/Vue, so the runtime package is intentionally not installed. These interaction principles are implemented with native Vue controls and project tokens.

The account forms also follow the inspected XDS `TextInput` and `FormLayout` guidance: persistent visible labels, a vertical reading order, field-linked errors, autocomplete metadata, one primary submit action, and an explicit loading state.

## Spec/Test/Code/Review/Ship Trace

- Spec: `docs/prd.md`, `docs/architecture.md`, this document
- Test: backend scoring/API tests and frontend state tests
- Code: `backend/`, `frontend/`
- Review: `review/checklist.md` and `VERIFY.md`
- Ship: locally verified account and recommendation application, with GitHub/Vercel/Neon production configuration prepared for live verification
