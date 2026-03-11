---
phase: 15-whatsapp-permanent-token-user-phone-number-in-settings-real-time-chat-message-polling
plan: "01"
subsystem: ui
tags: [react, typescript, whatsapp, preferences, e164, phone-validation]

# Dependency graph
requires:
  - phase: 02-infrastructure-user-management
    provides: PUT /preferences/whatsapp endpoint accepting PhoneLinkRequest { phone }
  - phase: 06-web-app-multi-platform
    provides: SettingsPage component and preferences.ts API layer
provides:
  - linkWhatsApp(token, phone) function in preferences.ts calling PUT /preferences/whatsapp
  - Conditional phone number input in SettingsPage when preferred_platform === 'whatsapp'
  - E.164 phone validation in frontend before API call
  - Phone pre-populated from prefs.whatsapp_phone on page load
affects: [whatsapp-routing, preferences, settings-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Conditional input pattern: render extra input when specific platform toggle is active"
    - "Pre-save validation guard: validate + setError + early return before any API call"
    - "Ordered save: call platform-specific endpoint (linkWhatsApp) before generic PATCH /preferences/"

key-files:
  created: []
  modified:
    - frontend/src/api/preferences.ts
    - frontend/src/pages/SettingsPage.tsx

key-decisions:
  - "linkWhatsApp calls PUT /preferences/whatsapp (not PATCH /preferences/) — whatsapp_phone is NOT accepted by PreferencesPatchRequest (backend returns 422)"
  - "Phone input only shown when preferred_platform === 'whatsapp' — controlled by prefs state, not local toggle"
  - "phoneError clears on every keystroke to avoid stale error messages"
  - "linkWhatsApp called before updatePreferences in handleSave — phone linking precedes general prefs update"
  - "Phone field uses ?? '' fallback for undefined whatsapp_phone — prevents uncontrolled input warning"

patterns-established:
  - "Platform-conditional input: conditional JSX after platform toggle buttons inside same GlassCard"
  - "E.164 validation: /^\\+[0-9]{7,15}$/ regex check before API call with inline error display"

requirements-completed: [WA-01, WA-02]

# Metrics
duration: 7min
completed: 2026-03-11
---

# Phase 15 Plan 01: WhatsApp Phone Number in Settings Summary

**E.164 phone number input added to SettingsPage WhatsApp toggle — calls PUT /preferences/whatsapp before PATCH /preferences/ on save, with inline validation and pre-population from stored prefs**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-11T15:21:29Z
- **Completed:** 2026-03-11T15:28:35Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `linkWhatsApp(token, phone)` exported from preferences.ts — calls PUT /preferences/whatsapp with `{ phone }` JSON body
- SettingsPage conditionally shows a phone input field when WhatsApp platform is selected
- E.164 validation (`/^\+[0-9]{7,15}$/`) blocks save and shows inline error for invalid input
- Phone pre-populated from `prefs.whatsapp_phone` on page load (handles undefined gracefully with `?? ''`)
- Save flow: invalid E.164 → set phoneError + return early; valid → linkWhatsApp then updatePreferences

## Task Commits

Each task was committed atomically:

1. **Task 1: Add linkWhatsApp() to preferences.ts** - `cbbe991` (feat)
2. **Task 2: Add conditional phone number input to SettingsPage** - `9de7e80` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `frontend/src/api/preferences.ts` - Added `linkWhatsApp(token, phone)` function (PUT /preferences/whatsapp)
- `frontend/src/pages/SettingsPage.tsx` - Added phoneNumber/phoneError state, isValidE164 helper, updated handleSave, added conditional phone input JSX

## Decisions Made
- PUT /preferences/whatsapp is the only correct path for phone linking — whatsapp_phone is NOT accepted by PATCH /preferences/ (backend 422 on unknown field)
- Phone input conditional on `prefs.preferred_platform === 'whatsapp'` (prefs state) not a local toggle variable — consistent with rest of settings pattern
- linkWhatsApp called before updatePreferences — ensures phone is linked before general prefs are saved

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- WhatsApp phone number can now be linked via the Settings page
- linkWhatsApp() and phone validation are ready for use
- Phase 15 plans 02+ (permanent token, real-time polling) can proceed

---
*Phase: 15-whatsapp-permanent-token-user-phone-number-in-settings-real-time-chat-message-polling*
*Completed: 2026-03-11*
