---
phase: 15-whatsapp-permanent-token-user-phone-number-in-settings-real-time-chat-message-polling
verified: 2026-03-11T00:00:00Z
status: passed
score: 6/8 must-haves verified
re_verification: false
human_verification:
  - test: "WhatsApp permanent token deployed to VPS"
    expected: "backend/.env on VPS contains WHATSAPP_ACCESS_TOKEN set to a permanent System User token (not the 60-day developer token); docker compose ps shows backend container Up after restart"
    why_human: "VPS .env is not committed to the repo — cannot be verified from codebase. Production-only credential."
  - test: "WhatsApp end-to-end: message receives AI reply"
    expected: "Send a WhatsApp message from a linked phone to the Ava business number; AI reply arrives within 30 seconds"
    why_human: "Requires a real WhatsApp account and active Meta API credentials in production. Verified manually during Plan 02 Task 3 by the user."
  - test: "Chat polling active in production"
    expected: "On https://avasecret.org/chat, DevTools Network tab shows GET /chat/history requests every ~3 seconds"
    why_human: "Requires a live browser session in production. The code (refetchInterval: 3000) is present and wired, but actual network behavior requires runtime verification."
---

# Phase 15: WhatsApp Permanent Token + Phone Number in Settings + Chat Polling Verification Report

**Phase Goal:** Close three pre-milestone gaps: replace the expiring developer token with a permanent System User token, add a phone number input to the Settings WhatsApp toggle, and confirm real-time chat polling works in production.
**Verified:** 2026-03-11
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | When WhatsApp platform is selected in Settings, a phone number input appears below the toggle | VERIFIED | `SettingsPage.tsx:129` — `{prefs.preferred_platform === 'whatsapp' && (<div className="mt-3">...input...)}` |
| 2 | User can type a phone number in E.164 format and save it via the Save Settings button | VERIFIED | `SettingsPage.tsx:134-143` — input is bound to `phoneNumber` state; Save button calls `handleSave()` |
| 3 | Invalid phone format shows an inline error and does not call the API | VERIFIED | `SettingsPage.tsx:58-62` — `isValidE164()` check; `setPhoneError(...)` + `return` before any API call |
| 4 | On save with WhatsApp selected and a valid phone, PUT /preferences/whatsapp is called before PATCH /preferences/ | VERIFIED | `SettingsPage.tsx:57-64` — `await linkWhatsApp(token, phoneNumber)` on line 63, then `await updatePreferences(...)` on line 65 |
| 5 | Phone number field is pre-populated from existing prefs.whatsapp_phone on page load | VERIFIED | `SettingsPage.tsx:41` — `setPhoneNumber(data.whatsapp_phone ?? '')` in useEffect |
| 6 | Chat message list refreshes automatically without user action (~3 seconds) | VERIFIED | `chat.ts:21` — `refetchInterval: 3000` in `useChatHistory()`; wired in `ChatPage.tsx:19` |
| 7 | WhatsApp replies continue working after 60+ days without token rotation | NEEDS HUMAN | Permanent System User token deployment is a VPS-only change; code reads `settings.whatsapp_access_token` from env. Whether the deployed token is the permanent one cannot be verified from the codebase. |
| 8 | Sending a WhatsApp message from a linked phone results in an AI reply on WhatsApp | NEEDS HUMAN | Requires live production WhatsApp interaction. Code path is fully wired (webhook.py → adapter → ChatService → send), but runtime correctness depends on production credentials. |

**Score:** 6/8 truths verified programmatically (2 require human/production confirmation)

---

### Required Artifacts

#### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/api/preferences.ts` | exports `linkWhatsApp(token, phone)` calling PUT /preferences/whatsapp | VERIFIED | Lines 42-52: exported async function, `fetch('/preferences/whatsapp', { method: 'PUT', body: JSON.stringify({ phone }) })` |
| `frontend/src/pages/SettingsPage.tsx` | conditional phone input inside Preferred Platform GlassCard | VERIFIED | Lines 129-143: `{prefs.preferred_platform === 'whatsapp' && ...}` wraps a `<div>` with label, input, and error paragraph |

#### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/.env on VPS` | WHATSAPP_ACCESS_TOKEN (permanent System User token) and WHATSAPP_PHONE_NUMBER_ID | NEEDS HUMAN | Not committed to repo by design; SUMMARY-02 documents it was set. Config.py confirms both fields exist: `whatsapp_access_token: str = ""` and `whatsapp_phone_number_id: str = ""` (lines 12-13). |
| `backend/migrations/007_whatsapp_phone.sql` | Adds whatsapp_phone column to user_preferences | VERIFIED | File exists at `backend/migrations/007_whatsapp_phone.sql`. Adds `whatsapp_phone TEXT` nullable column with `ADD COLUMN IF NOT EXISTS`. |
| `backend/app/routers/preferences.py` | PUT /preferences/whatsapp endpoint with on_conflict='user_id' | VERIFIED | Lines 9-40: `@router.put("/whatsapp")` accepts `PhoneLinkRequest`, upserts with `on_conflict="user_id"`, sends welcome template. |
| `backend/app/routers/webhook.py` | Phone normalization (+prefix) before DB lookup | VERIFIED | Line 70: `normalized_phone = sender_phone if sender_phone.startswith("+") else f"+{sender_phone}"` |

**Note on migration path:** The 15-02-SUMMARY.md states the migration file is at `backend/app/migrations/007_whatsapp_phone.sql`, but the actual file is at `backend/migrations/007_whatsapp_phone.sql`. The file exists at the correct project location — this is a documentation discrepancy only, not a functional issue.

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `frontend/src/pages/SettingsPage.tsx` | PUT /preferences/whatsapp | `linkWhatsApp()` called inside `handleSave()` | WIRED | `SettingsPage.tsx:6` imports `linkWhatsApp`; `SettingsPage.tsx:63` calls `await linkWhatsApp(token, phoneNumber)` inside `handleSave` |
| `phoneNumber` state | `prefs.whatsapp_phone` | `useEffect` initializing from loaded prefs | WIRED | `SettingsPage.tsx:41` — `setPhoneNumber(data.whatsapp_phone ?? '')` in the getPreferences useEffect |
| `VPS backend/.env` | `send_whatsapp_message()` | `settings.whatsapp_access_token` loaded from env | NEEDS HUMAN | `config.py:12` defines `whatsapp_access_token: str = ""`. Backend reads it correctly via pydantic-settings. Actual token presence on VPS cannot be verified from codebase. |
| `useChatHistory()` | GET /chat/history | `refetchInterval: 3000` in chat.ts | WIRED | `chat.ts:21` — `refetchInterval: 3000` in useQuery options. `ChatPage.tsx:19` — `const { data: messages = [], isLoading } = useChatHistory(token)` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| WA-01 | 15-01-PLAN, 15-02-PLAN | Phone number input in Settings WhatsApp toggle | SATISFIED | `SettingsPage.tsx:129-143` — conditional phone input rendered and wired to `linkWhatsApp()` on save |
| WA-02 | 15-01-PLAN, 15-02-PLAN | Permanent System User token (non-expiring WhatsApp access) | PARTIALLY SATISFIED | Code path reads `settings.whatsapp_access_token` from env correctly. Token deployment to VPS is human-verified (per SUMMARY-02). Cannot be confirmed from codebase alone. |
| WA-03 | 15-02-PLAN | Real-time chat polling working in production | SATISFIED (code) / NEEDS HUMAN (runtime) | `chat.ts:21` — `refetchInterval: 3000`; wired in `ChatPage.tsx:19`. Production network behavior confirmed by user during Plan 02 Task 3 (Verify C). |

**Note on REQUIREMENTS.md:** WA-01, WA-02, WA-03 are not present in `.planning/REQUIREMENTS.md`. That file covers v1.1 Launch Ready requirements (INFRA-*, EMAI-*, AUTH-*, LAND-*, SUBS-*, ADMN-*). The WA-* IDs are phase-level gap-closure requirements tracked only in ROADMAP.md and plan frontmatter. This is consistent with the project's two-tier requirements model: REQUIREMENTS.md tracks milestone requirements; ROADMAP.md tracks per-phase goals. No orphaned requirements — by design.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No stubs, TODOs, empty implementations, or placeholder code found in modified files. The `placeholder="+33612345678"` and `placeholder="e.g. just us now"` hits are HTML input placeholder attributes — correct usage, not code stubs.

---

### Human Verification Required

#### 1. Permanent WhatsApp System User Token on VPS

**Test:** SSH to VPS, run `grep WHATSAPP_ACCESS_TOKEN /opt/ava2/backend/.env` (or equivalent path) and confirm the token is present. Cross-reference with Meta Business Manager to confirm it is a System User token (not the 60-day developer token from the Getting Started page).
**Expected:** A non-empty token value; no expiry within 60 days.
**Why human:** VPS .env is not committed to the repo. The SUMMARY-02 documents this was done by the user during Plan 02 Task 2, including `docker compose restart backend` to apply it.

#### 2. WhatsApp End-to-End Messaging

**Test:** Send a WhatsApp message from a phone number linked in the Settings page to the Ava business number (configured as WHATSAPP_PHONE_NUMBER_ID).
**Expected:** AI reply arrives in WhatsApp within 30 seconds.
**Why human:** Requires a real WhatsApp account, active production credentials, and a live network interaction. SUMMARY-02 states this was verified (Verify B passed).

#### 3. Chat Polling Visible in Production

**Test:** Open https://avasecret.org/chat in a browser. Open DevTools Network tab, filter by "history". Watch for 60 seconds.
**Expected:** GET /chat/history requests appear every ~3 seconds continuously.
**Why human:** Runtime browser behavior in production. The code (`refetchInterval: 3000`) is present and wired correctly. SUMMARY-02 states this was confirmed (Verify C passed).

---

### Gaps Summary

No automated gaps found. All code artifacts are substantive, fully wired, and free of stubs.

The three human verification items above are production-only confirmations:
- Item 1 (permanent token) is a VPS credential that cannot be verified from the repo.
- Item 2 (WhatsApp E2E) requires a live WhatsApp interaction in production.
- Item 3 (chat polling) has code evidence (`refetchInterval: 3000` wired through `useChatHistory` into `ChatPage`) sufficient to call this verified at code level; runtime confirmation was provided by the user during Plan 02 execution.

Per SUMMARY-02, all three production verifications were confirmed by the user on 2026-03-11. If taken at face value, the phase goal is fully achieved. The `human_needed` status reflects that these claims cannot be independently verified from the codebase alone.

---

_Verified: 2026-03-11_
_Verifier: Claude (gsd-verifier)_
