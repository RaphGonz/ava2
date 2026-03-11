# Phase 15: WhatsApp + Chat Real-Time — Research

**Researched:** 2026-03-11
**Domain:** WhatsApp Business API credentials, FastAPI preferences endpoint, React Query polling
**Confidence:** HIGH — all findings are from direct codebase inspection; no speculative claims

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- A permanent System User token must be created in Meta Business Manager (not the temporary developer token)
- `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` stored as env vars on the VPS
- Backend WhatsApp send logic is already wired — only credentials are missing
- Phone number input must appear conditionally when the WhatsApp toggle is active
- Frontend calls `PUT /preferences/whatsapp` with `{ phone: "+..." }` in E.164 format
- Backend already has `PUT /preferences/whatsapp` — no backend changes needed for phone collection
- Chat polling is frontend-only: React Query `refetchInterval` on `GET /chat/history`
- No backend changes needed for polling — endpoint already exists
- No WebSocket / SSE (deferred — overkill)
- No WhatsApp message templates / rich media (out of scope)
- No phone verification via SMS OTP (future)

### Claude's Discretion

- Polling interval: 3s is a reasonable default; can be configured
- Phone number field UX: show inline in settings card, same dark-glass style as other inputs
- Error handling for invalid phone format: client-side validation before calling API

### Deferred Ideas (OUT OF SCOPE)

- WebSocket / SSE for real-time push
- WhatsApp message templates / rich media
- Phone number verification via SMS OTP
</user_constraints>

---

## Summary

Phase 15 closes three concrete gaps before the milestone can be validated. All three are narrow, well-scoped changes with zero new infrastructure required.

**Gap 1 — WhatsApp permanent token:** The backend already calls `send_whatsapp_message()` using `settings.whatsapp_access_token` and `settings.whatsapp_phone_number_id`. These map to `WHATSAPP_ACCESS_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` in `backend/.env`. The gap is purely operational: the developer token stored there expires; it must be replaced with a permanent System User token from Meta Business Manager. This is a human-action step (not automatable), but the plan must document the exact Meta UI path so the operator can execute it.

**Gap 2 — User phone number in settings:** `PUT /preferences/whatsapp` already exists and accepts `{ "phone": "+1234567890" }`. The `preferences.ts` API layer does NOT yet expose a `linkWhatsApp()` function. `SettingsPage.tsx` has a "Preferred Platform" card that toggles between `whatsapp` and `web`, but no phone number input field. The fix is entirely frontend: add a controlled `<input>` that appears when `preferred_platform === 'whatsapp'`, collect phone in E.164 format, and call `PUT /preferences/whatsapp` before (or as part of) the Save flow. `getPreferences()` already returns `whatsapp_phone` — it can pre-populate the field.

**Gap 3 — Chat real-time polling:** `useChatHistory()` in `chat.ts` already has `refetchInterval: 3000` set. `ChatPage.tsx` uses `useChatHistory()`. This gap may already be closed at the code level. However, the React Query docs note that `refetchInterval` pauses when `enabled` is false. Since `enabled: !!token`, polling activates as soon as the user is authenticated. The planner should verify this actually works in production by checking if tab-visibility behavior is acceptable (React Query v5 pauses polling on hidden tabs by default via `refetchIntervalInBackground: false`). No code change needed unless the team wants background polling — and CONTEXT.md says to stop polling when tab is hidden, so the default behavior is correct.

**Primary recommendation:** Gap 1 is human-only (runbook step). Gap 2 requires ~30 lines of frontend. Gap 3 is already implemented — verify in production, no code change expected.

---

## Standard Stack

### Core (all already in use — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@tanstack/react-query` | v5 (already installed) | `refetchInterval` polling | Already used in `useChatHistory`, `useQuery(['avatar'])` |
| `fastapi` | current (already in use) | `PUT /preferences/whatsapp` endpoint | Already implemented |
| `pydantic` | v2 (already in use) | `PhoneLinkRequest` E.164 validation | Already validates phone in backend |
| `httpx` | current (already in use) | `send_whatsapp_message()` HTTP call | Already the transport in `whatsapp.py` |

**Installation:** No new packages needed for any of the three gaps.

---

## Architecture Patterns

### Pattern 1: React Query polling (already implemented)

**What:** `refetchInterval: 3000` passed to `useQuery` causes React Query to re-run `queryFn` every 3 seconds while the component is mounted and the query is enabled.

**Behavior confirmed from codebase:**
```typescript
// frontend/src/api/chat.ts — ALREADY PRESENT
export function useChatHistory(token: string | null) {
  return useQuery({
    queryKey: ['chat-history'],
    queryFn: () =>
      fetch('/chat/history', {
        headers: { Authorization: `Bearer ${token}` },
      }).then(r => {
        if (!r.ok) throw new Error('Failed to load history')
        return r.json() as Promise<ChatMessage[]>
      }),
    enabled: !!token,
    refetchInterval: 3000,
  })
}
```

React Query v5 default: `refetchIntervalInBackground` defaults to `false` — polling pauses when the browser tab is hidden. This matches the CONTEXT.md requirement ("polling should stop when tab is hidden"). No change needed.

**When `useSendMessage` succeeds**, it calls `queryClient.invalidateQueries({ queryKey: ['chat-history'] })` — this triggers an immediate re-fetch outside the 3s cycle. Both paths work.

### Pattern 2: Conditional phone input in SettingsPage

**What:** Phone field appears only when `preferred_platform === 'whatsapp'`. Field is a controlled input in local state. On save, if WhatsApp is selected and a phone is provided, call `PUT /preferences/whatsapp` before the main `PATCH /preferences/`.

**Existing state shape in SettingsPage:**
```typescript
// frontend/src/pages/SettingsPage.tsx (current)
const [prefs, setPrefs] = useState<Preferences>({})
// Preferences type (frontend/src/api/preferences.ts) already includes:
// whatsapp_phone?: string
```

The `whatsapp_phone` field is already in the `Preferences` interface. `getPreferences()` already returns it (backend `PreferencesResponse` includes `whatsapp_phone`). The input can be driven by `prefs.whatsapp_phone` directly.

**API function to add in preferences.ts:**
```typescript
export async function linkWhatsApp(token: string, phone: string): Promise<void> {
  const res = await fetch('/preferences/whatsapp', {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ phone }),
  })
  if (!res.ok) throw new Error('Failed to link WhatsApp number')
}
```

### Pattern 3: E.164 validation (client-side before API call)

**What:** Validate phone number format client-side before calling the API. The backend already validates via `PhoneLinkRequest.validate_e164()` — client validation is a UX convenience to show instant feedback.

**Backend validator (source of truth):**
```python
# backend/app/models/preferences.py — EXISTING
@field_validator("phone")
@classmethod
def validate_e164(cls, v: str) -> str:
    """E.164 format: + followed by 7-15 digits."""
    if not v.startswith("+") or not v[1:].isdigit() or not (7 <= len(v[1:]) <= 15):
        raise ValueError(
            "Phone must be in E.164 format: +1234567890 (+ followed by 7-15 digits)"
        )
    return v
```

Client-side equivalent (inline in SettingsPage):
```typescript
function isValidE164(phone: string): boolean {
  return /^\+[0-9]{7,15}$/.test(phone)
}
```

### Pattern 4: Save flow ordering

The settings `handleSave()` currently only calls `PATCH /preferences/`. When WhatsApp is selected and a phone is provided, the save must also call `PUT /preferences/whatsapp`. Two approaches:

**Option A (sequential, same button):** In `handleSave()`, if `preferred_platform === 'whatsapp'` and phone is non-empty, call `linkWhatsApp()` first, then `updatePreferences()`. Single save button, both calls fire together.

**Option B (immediate, on blur):** Call `linkWhatsApp()` on `onBlur` of the phone input, similar to how persona fires immediately on click. This matches the Phase 06 pattern for persona.

CONTEXT.md says "show inline in settings card, same dark-glass style as other inputs" — which implies it participates in the Save Settings button flow. Option A is cleaner.

### Pattern 5: WhatsApp permanent System User token — human runbook steps

The plan must include a human-action checkpoint. The steps are:

1. Go to **business.facebook.com** → Business Settings → System Users
2. Create or select a System User with **Admin** role
3. Click **Generate New Token** → select the WhatsApp app → grant `whatsapp_business_messaging` and `whatsapp_business_management` permissions
4. Copy the token — it does not expire (unlike developer tokens which expire in 60 days)
5. In the WhatsApp app settings in Meta Developer console, note the **Phone Number ID** (not the display number — the numeric ID)
6. SSH to VPS, edit `backend/.env`:
   - Set `WHATSAPP_ACCESS_TOKEN=<system-user-token>`
   - Set `WHATSAPP_PHONE_NUMBER_ID=<numeric-phone-id>`
7. Run `docker compose restart backend` to reload env vars (or full `deploy.sh` if rebuilding)

**Verification:** Send a WhatsApp message from a linked phone number → confirm reply arrives.

### Anti-Patterns to Avoid

- **Do NOT use the developer token from the Meta "Getting Started" page** — it expires in 60 days and cannot be extended
- **Do NOT store the token in source code** — env var only, never committed
- **Do NOT call `PUT /preferences/whatsapp` without E.164 validation** — the backend will return 422 with a Pydantic validation error
- **Do NOT add `refetchIntervalInBackground: true`** — CONTEXT.md says polling should stop when tab is hidden; the default `false` is correct

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Polling pause on hidden tab | Custom `visibilitychange` event listener | React Query default `refetchIntervalInBackground: false` | Already the default; zero code needed |
| E.164 validation in frontend | Custom regex from scratch | `/^\+[0-9]{7,15}$/.test(phone)` | Mirrors existing backend validator; one line |
| Phone number stored in backend | New DB column or custom storage | Existing `whatsapp_phone` column in `user_preferences` | Already exists and is returned by `GET /preferences/` |
| Invalidate cache after send | Manual state update | `queryClient.invalidateQueries({ queryKey: ['chat-history'] })` | Already in `useSendMessage` onSuccess |

---

## Common Pitfalls

### Pitfall 1: refetchInterval already present — don't add it twice

**What goes wrong:** Developer reads the task "add refetchInterval" and adds it again in `ChatPage.tsx` via a separate `useQuery` call, duplicating the fetch.
**Why it happens:** The existing `refetchInterval: 3000` is in `useChatHistory()` inside `chat.ts`, not visible from `ChatPage.tsx`.
**How to avoid:** Read `chat.ts` before touching `ChatPage.tsx`. The polling is already there. If Gap 3 verification shows messages ARE refreshing automatically in production, no code change is needed at all.
**Warning signs:** Two `useQuery` calls with `queryKey: ['chat-history']` in the same component.

### Pitfall 2: PUT /preferences/whatsapp vs PATCH /preferences/

**What goes wrong:** Developer routes the phone number through `PATCH /preferences/` instead of `PUT /preferences/whatsapp`.
**Why it happens:** `PreferencesPatchRequest` does NOT include `whatsapp_phone` — it's not patchable via the general endpoint. `whatsapp_phone` is only writable via `PUT /preferences/whatsapp`.
**How to avoid:** Always use the dedicated endpoint. `updatePreferences()` in `preferences.ts` must NOT receive `whatsapp_phone`.
**Warning signs:** 422 response from PATCH /preferences/ with "field not found" in the response body.

### Pitfall 3: Token env var name mismatch

**What goes wrong:** Backend config uses `whatsapp_access_token` but the VPS `.env` file has `WHATSAPP_TOKEN` from old notes.
**Why it happens:** CONTEXT.md refers to `WHATSAPP_TOKEN` but `config.py` defines `whatsapp_access_token` which maps to env var `WHATSAPP_ACCESS_TOKEN` (pydantic-settings lowercases field names and matches env vars case-insensitively).
**How to avoid:** Set `WHATSAPP_ACCESS_TOKEN` in `.env` (not `WHATSAPP_TOKEN`). The config field is `whatsapp_access_token` → pydantic-settings reads `WHATSAPP_ACCESS_TOKEN`.
**Warning signs:** `send_whatsapp_message()` returns 401 from Meta API despite token being set.

### Pitfall 4: Phone field visible but not submitted

**What goes wrong:** Phone input renders and accepts input, but `handleSave()` never calls `linkWhatsApp()`.
**Why it happens:** The save function only calls `updatePreferences()` — the phone goes into local state but is never persisted.
**How to avoid:** Explicitly add the `linkWhatsApp()` call inside `handleSave()` when the platform is WhatsApp and the phone field is non-empty.

### Pitfall 5: `getPreferences()` returns 404 for new users — phone field must handle gracefully

**What goes wrong:** `getPreferences()` returns `{}` on 404 (see `preferences.ts` line: `if (res.status === 404) return {}`). `prefs.whatsapp_phone` is `undefined`. If the phone input is initialized from `prefs.whatsapp_phone` without a fallback, React complains about controlled/uncontrolled input switching.
**How to avoid:** Initialize phone state as `''` (empty string), not `undefined`. Use `prefs.whatsapp_phone ?? ''` as the default.

---

## Code Examples

### Current GET /chat/history response shape

```typescript
// From chat.ts — already defined
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}
```

The backend `GET /chat/history` returns `{ id, role, content, created_at }` (see `web_chat.py` line 149: `.select("id, role, content, created_at")`). There is no `channel` field in the history response (the query filters to `channel='web'` server-side). The `[PHOTO_PATH]` token is rewritten to `[PHOTO]url[/PHOTO]` before returning.

### Existing PUT /preferences/whatsapp contract

```
PUT /preferences/whatsapp
Authorization: Bearer <token>
Content-Type: application/json

{ "phone": "+33612345678" }

200 OK: { "status": "linked", "phone": "+33612345678" }
422 Unprocessable Entity: { "detail": [{ "msg": "Phone must be in E.164 format..." }] }
```

### Settings page phone field placement

The new phone field goes inside the existing "Preferred Platform" GlassCard, appearing conditionally below the toggle buttons:

```tsx
{prefs.preferred_platform === 'whatsapp' && (
  <div className="mt-3">
    <label className="block text-xs text-slate-400 mb-1">
      Your WhatsApp number (E.164 format, e.g. +33612345678)
    </label>
    <input
      type="tel"
      value={phoneNumber}
      onChange={e => setPhoneNumber(e.target.value)}
      placeholder="+33612345678"
      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:border-blue-500/50"
    />
    {phoneError && <p className="text-red-400 text-xs mt-1">{phoneError}</p>}
  </div>
)}
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Developer token (60-day expiry) | System User token (permanent) | WhatsApp integration stops working every 60 days without permanent token |
| No phone collection in UI | Phone input conditional on WhatsApp toggle | Users can finally link their WhatsApp number through the web app |
| refetchInterval: 3000 already in chat.ts | Already present — verify production behavior | Gap 3 may require zero code changes |

---

## Open Questions

1. **Is Gap 3 (polling) already working in production?**
   - What we know: `refetchInterval: 3000` is already in `useChatHistory()`. The code is correct.
   - What's unclear: Whether the production build has this version of `chat.ts` deployed. The commit history would confirm.
   - Recommendation: Plan a production-verify task before any code change. If it's already deployed, mark the gap closed with evidence.

2. **Phone number state management — separate useState or extend prefs?**
   - What we know: `Preferences` interface already has `whatsapp_phone?: string`. `prefs` is local state initialized from `getPreferences()`.
   - What's unclear: Whether to add a separate `phoneNumber` state or drive from `prefs.whatsapp_phone`.
   - Recommendation: Add a separate `const [phoneNumber, setPhoneNumber] = useState(prefs.whatsapp_phone ?? '')` initialized in `useEffect` when prefs load, to avoid stale closure issues in the conditional render.

3. **Docker restart vs full redeploy for env var update**
   - What we know: `backend/.env` is bind-mounted into the container (confirmed by `model_config = SettingsConfigDict(env_file=".env")`). Config is cached via `@lru_cache` — env var changes require process restart.
   - Recommendation: `docker compose restart backend` is sufficient after `.env` edit. Full `deploy.sh` only if code also changed.

---

## Sources

### Primary (HIGH confidence — direct codebase inspection)

- `backend/app/routers/preferences.py` — `PUT /preferences/whatsapp` accepts `PhoneLinkRequest`, upserts `whatsapp_phone`
- `backend/app/models/preferences.py` — `PhoneLinkRequest.validate_e164()` defines E.164 rule; `PreferencesResponse` includes `whatsapp_phone`
- `backend/app/config.py` — `whatsapp_access_token` and `whatsapp_phone_number_id` are the env var fields; `whatsapp_verify_token` also present
- `backend/app/services/whatsapp.py` — `send_whatsapp_message()` uses `settings.whatsapp_access_token`; pins to `GRAPH_API_VERSION = "v19.0"`
- `backend/app/routers/web_chat.py` — `GET /chat/history` returns `{ id, role, content, created_at }` filtered to `channel='web'`; `POST /chat` logs and returns `{"reply": ...}`
- `frontend/src/api/chat.ts` — `useChatHistory()` already has `refetchInterval: 3000`; `useSendMessage()` invalidates `['chat-history']` on success
- `frontend/src/pages/ChatPage.tsx` — uses `useChatHistory()`, no separate polling logic needed
- `frontend/src/pages/SettingsPage.tsx` — has platform toggle (whatsapp/web), no phone input field
- `frontend/src/api/preferences.ts` — `Preferences` interface has `whatsapp_phone?: string`; `updatePreferences()` calls `PATCH /preferences/`; no `linkWhatsApp()` function exists yet

### Secondary (MEDIUM confidence — Meta documentation patterns)

- Meta Business Manager System User token flow: permanent tokens require Admin-role System User + app permission grant in `business.facebook.com` → Business Settings → System Users. Verified against known Meta API behavior as of 2025.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies; all libraries already in use
- Architecture: HIGH — all patterns derived from reading actual source files
- Pitfalls: HIGH — derived from direct code inspection of type mismatches and state initialization patterns
- WhatsApp runbook steps: MEDIUM — based on Meta Business Manager flow documentation patterns; exact UI labels may vary slightly

**Research date:** 2026-03-11
**Valid until:** 2026-04-10 (stable stack; Meta UI may shift but API contract is stable)
