---
phase: 06-web-app-multi-platform
plan: 02
subsystem: ui
tags: [react, vite, tailwind, zustand, tanstack-query, react-router-dom, typescript, jwt]

# Dependency graph
requires:
  - phase: 06-web-app-multi-platform
    provides: DB migration with message_channel 'web' and user_preferences columns

provides:
  - React + Vite + TypeScript + Tailwind v4 frontend scaffold at frontend/
  - Zustand auth store persisting JWT token and user_id to localStorage
  - API client modules for auth, chat, and preferences
  - LoginPage with email/password form wired to /auth/signin
  - App.tsx with ProtectedRoute guard and react-router-dom routing
  - Vite dev server proxy for /auth, /chat, /preferences, /avatars, /photos -> localhost:8000

affects:
  - 06-web-app-multi-platform plan 03 and above (all frontend UI plans build on this scaffold)

# Tech tracking
tech-stack:
  added:
    - react@19.2.0
    - react-dom@19.2.0
    - react-router-dom@7.13.1
    - "@tanstack/react-query@5.90.21"
    - zustand@5.0.11
    - tailwindcss@4.2.1 (CSS-based config, no tailwind.config.js)
    - "@tailwindcss/vite@4.2.1"
    - vite@7.3.1
    - typescript~5.9.3
  patterns:
    - Zustand persist middleware for auth state in localStorage under key 'ava-auth'
    - JWT payload base64url decode to extract sub claim as user_id (no /auth/me call)
    - TanStack Query hooks (useQuery/useMutation) for all server-state data fetching
    - Vite proxy config for same-origin API calls in dev (no CORS configuration needed)
    - ProtectedRoute component pattern using token check from useAuthStore

key-files:
  created:
    - frontend/package.json
    - frontend/vite.config.ts
    - frontend/index.html
    - frontend/src/main.tsx
    - frontend/src/App.tsx
    - frontend/src/index.css
    - frontend/src/store/useAuthStore.ts
    - frontend/src/api/auth.ts
    - frontend/src/api/chat.ts
    - frontend/src/api/preferences.ts
    - frontend/src/pages/LoginPage.tsx
    - frontend/src/pages/ChatPage.tsx (stub)
    - frontend/src/pages/SettingsPage.tsx (stub)
    - frontend/src/pages/PhotoPage.tsx (stub)
  modified: []

key-decisions:
  - "JWT payload decoded client-side (atob on base64url middle segment) to extract sub as user_id — avoids adding /auth/me endpoint or modifying backend in this plan"
  - "Tailwind v4 CSS-based config: no tailwind.config.js; single @import 'tailwindcss' directive in index.css with @tailwindcss/vite plugin"
  - "Vite dev proxy forwards /auth, /chat, /preferences, /avatars, /photos to localhost:8000 — frontend never needs CORS headers during development"
  - "Stub pages (ChatPage, SettingsPage, PhotoPage) created as minimal exports so App.tsx compiles; full implementation deferred to Plans 04 and 05"

patterns-established:
  - "useAuthStore pattern: Zustand store with persist middleware — import useAuthStore(s => s.token) to check auth in any component"
  - "API client pattern: plain fetch functions in src/api/ modules; TanStack Query hooks wrap them for server state management"
  - "ProtectedRoute pattern: check token from useAuthStore, redirect to /login if null"

requirements-completed: [PLAT-02]

# Metrics
duration: 20min
completed: 2026-02-24
---

# Phase 6 Plan 02: Frontend Scaffold Summary

**React 19 + Vite 7 + Tailwind v4 frontend with Zustand auth store, TanStack Query API clients, and LoginPage wired to existing /auth/signin FastAPI endpoint**

## Performance

- **Duration:** 20 min
- **Started:** 2026-02-24T16:01:04Z
- **Completed:** 2026-02-24T16:21:00Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments

- Created complete frontend/ scaffold with Vite 7, React 19, TypeScript 5.9, and Tailwind v4 (CSS-based config)
- Zustand auth store with persist middleware saves token + userId to localStorage under key 'ava-auth'
- Three API client modules (auth.ts, chat.ts, preferences.ts) with TanStack Query hooks for all server-state operations
- LoginPage with styled Tailwind form, error handling, loading state, and successful navigation to /chat on sign-in
- App.tsx routing with ProtectedRoute guard redirecting unauthenticated users to /login
- `npm run build` passes with zero TypeScript errors, dist/ generated

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold Vite + React + Tailwind frontend project** - `2542087` (feat)
2. **Task 2: Zustand auth store, API clients, and LoginPage** - `a252919` (feat)

## Files Created/Modified

- `frontend/package.json` - Project config; React 19, Vite 7, Tailwind v4, Zustand 5, TanStack Query 5, react-router-dom 7
- `frontend/vite.config.ts` - @tailwindcss/vite plugin + dev server proxy for all API paths
- `frontend/src/index.css` - Single line: `@import "tailwindcss"` (Tailwind v4 approach)
- `frontend/src/App.tsx` - BrowserRouter + QueryClientProvider + ProtectedRoute + all routes
- `frontend/src/main.tsx` - StrictMode root render (unchanged from Vite template)
- `frontend/src/store/useAuthStore.ts` - Zustand store with persist: token, userId, setAuth, clearAuth
- `frontend/src/api/auth.ts` - signIn() with JWT decode for user_id extraction; signOut() (client-only)
- `frontend/src/api/chat.ts` - useChatHistory() and useSendMessage() TanStack Query hooks
- `frontend/src/api/preferences.ts` - getPreferences() and updatePreferences() for /preferences/ endpoint
- `frontend/src/pages/LoginPage.tsx` - Email/password form, error display, loading state, navigates to /chat
- `frontend/src/pages/ChatPage.tsx` - Stub: "Chat coming soon"
- `frontend/src/pages/SettingsPage.tsx` - Stub: "Settings coming soon"
- `frontend/src/pages/PhotoPage.tsx` - Stub: "Photo viewer"

## Decisions Made

- **JWT client-side decode for user_id:** The existing `/auth/signin` endpoint returns `{access_token, token_type}` but not `user_id`. Rather than modifying the backend or adding `/auth/me`, the JWT payload's `sub` claim is extracted via `atob()` on the base64url middle segment. This is safe since the token is already validated server-side on every request.
- **Tailwind v4 CSS-first config:** No `tailwind.config.js` needed — `@import "tailwindcss"` in `index.css` and the `@tailwindcss/vite` plugin handle everything.
- **Vite proxy for same-origin feel:** All `/auth`, `/chat`, `/preferences`, `/avatars`, `/photos` calls are proxied to `localhost:8000` during dev, so frontend code uses plain `/auth/signin` paths with no CORS complexity.

## Deviations from Plan

None — plan executed exactly as written. All files created per specification, build passes, verification criteria met.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Frontend runs with `npm run dev` from `frontend/` once backend is running on port 8000.

## Next Phase Readiness

- Frontend scaffold complete; Plans 03, 04, 05 (AvatarSetup, ChatUI, SettingsUI) can now build on this base
- Dev server: `cd frontend && npm run dev` (runs on port 3000, proxies to backend on 8000)
- LoginPage is functional end-to-end once backend is running with valid Supabase credentials

## Self-Check: PASSED

All files verified present. All task commits confirmed in git history.

- FOUND: frontend/src/store/useAuthStore.ts
- FOUND: frontend/src/api/auth.ts
- FOUND: frontend/src/api/chat.ts
- FOUND: frontend/src/api/preferences.ts
- FOUND: frontend/src/pages/LoginPage.tsx
- FOUND: frontend/vite.config.ts
- FOUND: frontend/package.json
- FOUND: frontend/src/App.tsx
- FOUND: .planning/phases/06-web-app-multi-platform/06-02-SUMMARY.md
- COMMIT 2542087: feat(06-02): scaffold Vite + React + TypeScript + Tailwind v4 frontend
- COMMIT a252919: feat(06-02): add Zustand auth store, API clients, and LoginPage

---
*Phase: 06-web-app-multi-platform*
*Completed: 2026-02-24*
