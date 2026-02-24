---
phase: 06-web-app-multi-platform
plan: 05
subsystem: ui
tags: [react, tailwind, tanstack-query, zustand, typescript, chat-ui, settings-ui]

# Dependency graph
requires:
  - phase: 06-02
    provides: React/Vite scaffold, useAuthStore, API client modules (chat.ts, preferences.ts), stub pages
  - phase: 06-04
    provides: POST /chat, GET /chat/history, PATCH /preferences/, updatePersona PATCH /avatars/me/persona

provides:
  - ChatBubble: role-based message bubble (user right/dark, assistant left/light)
  - MessageList: scrollable message list with auto-scroll and loading state
  - ChatInput: textarea with Enter-to-send and send button
  - ChatPage: full chat interface (header, MessageList, ChatInput, sign-out)
  - SettingsPage: persona selector, platform toggle, spiciness ceiling, mode-switch phrase, notification toggle, save+feedback
  - PhotoPage: full-screen dark photo viewer consuming ?url= query param with expiry notice
  - updatePersona(): PATCH /avatars/me/persona added to preferences.ts

affects:
  - 06-06 (any further settings or UI iteration builds on these pages)
  - 07 (photo generation phase: PhotoPage is the signed-URL landing page for photos)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Chat bubble layout using Tailwind flex + justify-end/justify-start for role-based alignment
    - useRef<HTMLDivElement> + scrollIntoView({ behavior: 'smooth' }) for auto-scroll on new messages
    - TanStack Query useMutation.isPending for disabling input during send
    - Inline persona update (no save button) via updatePersona() on click — immediate API call

key-files:
  created:
    - frontend/src/components/ChatBubble.tsx
    - frontend/src/components/MessageList.tsx
    - frontend/src/components/ChatInput.tsx
  modified:
    - frontend/src/pages/ChatPage.tsx
    - frontend/src/pages/SettingsPage.tsx
    - frontend/src/pages/PhotoPage.tsx
    - frontend/src/api/preferences.ts

key-decisions:
  - "ChatBubble uses rounded-br-sm / rounded-bl-sm to create the messenger-style 'tail' effect on the bubble corner closest to the speaker"
  - "MessageList uses useRef + scrollIntoView on messages dependency — no external library needed for auto-scroll"
  - "Persona selector applies immediately (no save needed) — persona is an avatar attribute updated via PATCH /avatars/me/persona, distinct from preferences saved via Save Settings button"
  - "notif_prefs treated as Record<string, unknown> — avoids tightly coupling the frontend to a specific notification schema that may evolve"

patterns-established:
  - "Chat component pattern: ChatBubble (presentational) + MessageList (layout/scroll) + ChatInput (controlled form) — each single-responsibility, composed in ChatPage"
  - "Immediate vs. deferred settings: persona updates fire immediately on click; platform/spiciness/phrase accumulate in local state and save together on button press"

requirements-completed: [PLAT-02, PLAT-04]

# Metrics
duration: 10min
completed: 2026-02-24
---

# Phase 6 Plan 05: Frontend UI — Chat Components, SettingsPage, and PhotoPage Summary

**React chat UI with role-aligned message bubbles, persona/platform/spiciness settings, and dark-chrome photo viewer consuming Supabase signed URLs**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-24T17:29:08Z
- **Completed:** 2026-02-24T17:38:55Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Created `components/` directory with three reusable chat components (ChatBubble, MessageList, ChatInput) replacing stub pages
- ChatPage: header with Ava avatar, Settings/Sign-out nav, scrollable message list with auto-scroll, Enter-to-send input
- SettingsPage: 6-option persona selector (immediate PATCH), platform toggle (WhatsApp/Web), 3-tier spiciness ceiling, mode-switch phrase text input, notification toggle, save+feedback
- PhotoPage: full-screen dark layout, image from `?url=` query param, back-to-chat button, 24h expiry notice
- Added `updatePersona()` to `preferences.ts` calling `PATCH /avatars/me/persona`
- `npm run build` passes with zero TypeScript errors across all new/modified files

## Task Commits

Each task was committed atomically:

1. **Task 1: Chat components and ChatPage** - `3624d4b` (feat)
2. **Task 2: SettingsPage and PhotoPage** - `3e754a8` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `frontend/src/components/ChatBubble.tsx` - Role-based message bubble; user=right/dark, assistant=left/light; optional timestamp display
- `frontend/src/components/MessageList.tsx` - Scrollable flex container; useRef auto-scroll on new messages; loading + empty states
- `frontend/src/components/ChatInput.tsx` - Controlled textarea; Enter sends (Shift+Enter newline); disabled during pending mutation
- `frontend/src/pages/ChatPage.tsx` - Full chat interface; replaces stub; consumes useChatHistory + useSendMessage hooks
- `frontend/src/pages/SettingsPage.tsx` - Full settings form; replaces stub; persona (immediate), platform/spiciness/phrase/notifs (saved together)
- `frontend/src/pages/PhotoPage.tsx` - Full-screen photo viewer; replaces stub; reads ?url= via useSearchParams
- `frontend/src/api/preferences.ts` - Added updatePersona() for PATCH /avatars/me/persona

## Decisions Made

- **ChatBubble corner styling:** `rounded-br-sm` on user bubbles and `rounded-bl-sm` on assistant bubbles creates the messenger "tail" effect pointing toward the speaker, achieved with Tailwind alone — no images needed.
- **Persona selector is immediate (no save):** Persona is an avatar attribute distinct from user_preferences. It calls `PATCH /avatars/me/persona` immediately on click, giving snappy feedback. Platform/spiciness/phrase are accumulated in local state and saved together.
- **notif_prefs as `Record<string, unknown>`:** Avoids tightly coupling the frontend to a specific notification schema that may evolve in later phases.

## Deviations from Plan

None - plan executed exactly as written. All files created per specification, build passes, all verification criteria met.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Frontend runs with `npm run dev` from `frontend/` once backend is running on port 8000.

## Next Phase Readiness

- Full frontend UI complete: Login, Chat, Settings, and Photo viewer pages all functional
- ChatPage consumes `POST /chat` and `GET /chat/history` — ready for end-to-end testing with running backend
- SettingsPage consumes `GET /preferences/`, `PATCH /preferences/`, and `PATCH /avatars/me/persona` — all wired
- PhotoPage is the landing page for Phase 7 photo delivery (signed URL passed via `?url=` query param)

## Self-Check: PASSED

All files verified present. Both task commits confirmed in git log.

- FOUND: frontend/src/components/ChatBubble.tsx
- FOUND: frontend/src/components/MessageList.tsx
- FOUND: frontend/src/components/ChatInput.tsx
- FOUND: frontend/src/pages/ChatPage.tsx
- FOUND: frontend/src/pages/SettingsPage.tsx
- FOUND: frontend/src/pages/PhotoPage.tsx
- FOUND: frontend/src/api/preferences.ts
- COMMIT 3624d4b: feat(06-05): add chat components and ChatPage
- COMMIT 3e754a8: feat(06-05): add SettingsPage, PhotoPage, and updatePersona API

---
*Phase: 06-web-app-multi-platform*
*Completed: 2026-02-24*
