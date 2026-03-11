# Phase 15: WhatsApp + Chat Real-Time — Context

**Gathered:** 2026-03-11
**Status:** Ready for planning
**Source:** Conversation context (user-provided)

<domain>
## Phase Boundary

Two independent bugs that must be fixed before the v1.1 milestone can be validated:

1. **WhatsApp integration gaps** — The WhatsApp Business API integration is incomplete: no permanent System User token has been created, no WhatsApp business phone number is configured, and the user settings page has a "contact via WhatsApp" toggle but never collects the user's actual phone number.

2. **Chat real-time display** — Messages (both sent and received) only appear in the chat UI after the user sends a new message. There is no automatic polling or push update — the message list is stale until the next user action.

</domain>

<decisions>
## Implementation Decisions

### WhatsApp — Permanent Token
- A permanent System User token must be created in the Meta Business Manager (not the temporary developer token)
- The token and WhatsApp business phone number ID must be stored as env vars on the VPS (`WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`)
- The backend already has the WhatsApp send logic wired — only the credentials are missing

### WhatsApp — User Phone Number in Settings
- The settings page currently has a "contact via WhatsApp" toggle (`preferred_platform: 'whatsapp'`) but no phone number input field
- A phone number input must be added to the settings UI (E.164 format, validated)
- The backend already has `PUT /preferences/whatsapp` accepting `PhoneLinkRequest` — the frontend just needs to call it
- The phone number field should appear conditionally when the WhatsApp toggle is active

### Chat Real-Time Polling
- The current web chat uses synchronous HTTP (POST /chat returns the AI reply inline) — the issue is not about receiving replies but about the message LIST not refreshing automatically
- The fix is frontend-only: poll GET /messages at a regular interval (e.g., every 3 seconds) when the chat page is active, or use React Query's `refetchInterval`
- No backend changes needed — GET /messages already exists and returns the full message history with RLS isolation
- Polling should stop when the tab is hidden / component unmounts to avoid unnecessary requests

### Claude's Discretion
- Polling interval: 3s is a reasonable default; can be configured
- Phone number field UX: show inline in settings card, same dark-glass style as other inputs
- Error handling for invalid phone format: client-side validation before calling API

</decisions>

<specifics>
## Specific Details

- Backend WhatsApp send endpoint: `backend/app/services/` or similar — already implemented
- Backend preferences endpoint: `PUT /preferences/whatsapp` accepts `{ phone_number: "+1234567890" }`
- Frontend settings page: `frontend/src/pages/SettingsPage.tsx` — has WhatsApp toggle, no phone field
- Frontend chat page: `frontend/src/pages/ChatPage.tsx` (or similar) — message list not auto-refreshing
- Messages endpoint: `GET /messages` — returns history, RLS-isolated per user
- Meta Business Manager System User token: must be created manually by user (not automatable) — this is a human-action checkpoint in the plan

</specifics>

<deferred>
## Deferred Ideas

- WebSocket / SSE for real-time push (overkill for current scale — polling is sufficient)
- WhatsApp message templates / rich media (out of scope for this phase)
- Phone number verification via SMS OTP (future enhancement)

</deferred>

---

*Phase: 15-whatsapp-permanent-token-user-phone-number-in-settings-real-time-chat-message-polling*
*Context gathered: 2026-03-11 from user conversation*
