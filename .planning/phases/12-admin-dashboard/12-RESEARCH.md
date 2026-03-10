# Phase 12: Admin Dashboard - Research

**Researched:** 2026-03-10
**Domain:** Admin access control, usage event emission, metrics aggregation (FastAPI + Supabase + React)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Metrics displayed:**
- 5 metrics: active users, messages sent, photos generated, active subscriptions, new signups
- Each metric shows three time windows side by side: 7d / 30d / all-time
- Data sources (mixed, not all from usage_events):
  - Active users (7d): auth.users last_sign_in_at
  - New signups: auth.users created_at
  - Active subscriptions: subscriptions table
  - Messages sent: usage_events (message_sent)
  - Photos generated: usage_events (photo_generated)
- Manual refresh only — no auto-refresh or polling

**Access control:**
- Non-admin navigating to /admin: silent redirect to /chat (no error message shown)
- Admin role assigned via Supabase user_metadata flag: `is_admin: true` (set manually in Supabase dashboard)
- Enforcement at both layers: backend API returns 403, frontend route guard redirects non-admins
- No visible link to /admin anywhere in the UI — URL-only access for operators

**Usage event wiring:**
- 4 required event types: `message_sent`, `photo_generated`, `mode_switch`, `subscription_created`
- Emission strategy: fire-and-forget, silent failure (event write errors are logged but never block the user action)
- Each event row includes `user_id` for future per-user analysis
- `usage_events` table already exists in production (created in Phase 8 migration) — wire emission points only, no schema changes needed

**Dashboard layout:**
- Stat cards grid — one card per metric, 5 cards total
- Each card displays the metric name and 7d / 30d / all-time values
- Page header: "Admin Dashboard" title + last-updated timestamp showing data freshness
- Style matches existing app (Tailwind, dark theme, existing card/component patterns)

### Claude's Discretion
- Card grid column count / responsive breakpoints
- Exact Tailwind classes and color choices within existing palette
- Loading state while metrics fetch
- Error state if the metrics query fails

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ADMN-01 | Operator can view key metrics: active users (7-day), messages sent, photos generated, active subscriptions, new signups | Backend `/admin/metrics` endpoint aggregates from auth.users, subscriptions, and usage_events via supabase_admin; frontend AdminPage renders 5 GlassCards with 3 time-window values each |
| ADMN-02 | Usage events logged to `usage_events` table: message_sent, photo_generated, mode_switch, subscription_created | Table already exists (migration 005); 4 emit points wired: chat.py (message_sent + mode_switch), processor.py (photo_generated — currently goes to audit_log, needs usage_events too), billing.py webhook (subscription_created) |
| ADMN-03 | `/admin` route restricted to admin role only — regular users receive 403 | Backend `require_admin` dependency reads `user_metadata.is_admin` from Supabase JWT; frontend `AdminRoute` guard reads same field from decoded JWT and redirects non-admins to /chat |
</phase_requirements>

---

## Summary

Phase 12 adds an internal operator dashboard and wires usage event emission across the codebase. The infrastructure is already in place: the `usage_events` table exists in Supabase (migration 005) with RLS blocking regular-user reads, `supabase_admin` is the established pattern for service-role DB writes, and the FastAPI dependency chain (`get_current_user`) provides the JWT from which admin status is read. The phase has three distinct sub-problems: (1) add a `require_admin` FastAPI dependency and a `/admin/metrics` endpoint, (2) wire 4 usage event emit points across `chat.py`, `processor.py`, and `billing.py`, and (3) build the frontend AdminPage with an `AdminRoute` guard and 5 metric cards.

The admin check reads `user_metadata.is_admin` from the Supabase JWT. This is set manually in the Supabase Dashboard per the STATE.md roadmap decision: "Admin role assigned via Supabase user_metadata flag: `is_admin: true`." The Supabase Python SDK's `auth.get_user(token)` call already used in `get_current_user` returns the full user object including `user_metadata` — no new auth infrastructure is needed. The frontend must decode the JWT client-side (same `atob` pattern already used for `user_id` extraction) or call a backend endpoint to get the flag.

Metrics aggregation uses `supabase_admin` with three distinct data sources: `auth.users` (queried via `supabase_admin.auth.admin.list_users()` for active-user and new-signup counts), the `subscriptions` table (for active subscription count), and `usage_events` (for message and photo counts). Time-window filtering for 7d/30d uses Supabase PostgREST `.gte("created_at", cutoff_iso)`. The "all-time" window omits the time filter entirely.

**Primary recommendation:** Build in 3 plans — (1) backend `require_admin` dependency + `/admin/metrics` endpoint, (2) wire all 4 usage event emit points, (3) frontend AdminPage + AdminRoute guard.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| supabase-py | already installed | Admin queries (auth.users, subscriptions, usage_events) | Established pattern — supabase_admin already used in all routers |
| FastAPI | already installed | `require_admin` dependency + `/admin/metrics` router | Consistent with all existing routers |
| React + @tanstack/react-query | already installed | Admin page data fetching with staleTime | Same pattern as BillingPage |
| GlassCard (internal) | existing component | Stat cards display | `frontend/src/components/ui/GlassCard.tsx` already exists |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Tailwind v4 | already installed | Styling the dashboard grid | CSS-first config (no tailwind.config.js) — matches all existing pages |
| lucide-react | already installed | Icons in page header | Used in BillingPage and ChatPage headers |
| Vitest + @testing-library/react | vitest ^4.0.18 | Frontend tests for AdminPage and AdminRoute | Same test setup as LandingPage.test.tsx |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| supabase_admin.auth.admin.list_users() | custom SQL via supabase_admin.rpc() | list_users() is the standard Python SDK method; avoids raw SQL for auth.users access |
| Reading is_admin from user_metadata | Supabase custom claims / app_metadata | user_metadata simpler for manual assignment; app_metadata more structured but requires same manual step — user_metadata chosen per STATE.md decision |

**No new installations required.** All libraries are already present in the project.

---

## Architecture Patterns

### Recommended Project Structure

New files only (no restructuring):
```
backend/app/
├── routers/
│   └── admin.py              # NEW: /admin/metrics endpoint + require_admin dependency
frontend/src/
├── pages/
│   └── AdminPage.tsx         # NEW: metrics dashboard with 5 stat cards
├── api/
│   └── admin.ts              # NEW: getAdminMetrics() API call
```

Emission points (modifications to existing files):
```
backend/app/
├── services/
│   └── chat.py               # MODIFY: emit message_sent + mode_switch after each reply
│   └── jobs/processor.py     # MODIFY: emit photo_generated to usage_events (currently only audit_log)
├── routers/
│   └── billing.py            # MODIFY: emit subscription_created in checkout.session.completed handler
```

App.tsx modification: add `AdminRoute` guard component + `/admin` route.

### Pattern 1: require_admin FastAPI Dependency

**What:** A FastAPI dependency that extends `get_current_user` by checking `user.user_metadata.get("is_admin")`. Raises HTTP 403 if not set. Used on all `/admin/*` endpoints.

**When to use:** Any endpoint that must be admin-only.

**Example:**
```python
# Source: Consistent with existing dependencies.py pattern
from fastapi import Depends, HTTPException, status
from app.dependencies import get_current_user

async def require_admin(user=Depends(get_current_user)):
    """
    Extends get_current_user — raises 403 if user lacks is_admin flag.
    Admin status set via Supabase Dashboard: user_metadata.is_admin = true.
    """
    is_admin = (user.user_metadata or {}).get("is_admin", False)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user
```

### Pattern 2: Usage Event Emission (Fire-and-Forget)

**What:** Inline `try/except` block after the user action completes. Writes to `usage_events` via `supabase_admin`. Errors are logged but never raised. Never blocks the user-facing reply.

**When to use:** At every emission point — after message reply returned, after mode switch, after photo job enqueued, after subscription activated.

**Example:**
```python
# Source: Established pattern already used in billing.py cancel endpoint
try:
    supabase_admin.from_("usage_events").insert({
        "user_id": user_id,
        "event_type": "message_sent",   # or "mode_switch" | "photo_generated" | "subscription_created"
        "metadata": {},                  # optional — add event-specific context if useful
    }).execute()
except Exception as exc:
    logger.error("Failed to emit usage event: %s", exc)
# Never raises — user action already completed above
```

### Pattern 3: Supabase Auth Admin List Users

**What:** `supabase_admin.auth.admin.list_users()` returns all users with `last_sign_in_at` and `created_at` fields. Filter in Python for time-window comparisons.

**When to use:** Active user count (last_sign_in_at >= 7d ago) and new signups (created_at >= 7d / 30d ago / all-time).

**Note:** The supabase-py SDK's `auth.admin.list_users()` returns a list of `User` objects. Pagination exists but at current scale (early launch) a single call is sufficient. Returns at most 1000 users per call by default.

**Example:**
```python
# Source: supabase-py auth.admin API
from datetime import datetime, timezone, timedelta

def _cutoff(days: int | None) -> datetime | None:
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)

users_response = supabase_admin.auth.admin.list_users()
all_users = users_response  # list of User objects

cutoff_7d = _cutoff(7)
active_7d = sum(
    1 for u in all_users
    if u.last_sign_in_at and u.last_sign_in_at >= cutoff_7d
)
new_7d = sum(
    1 for u in all_users
    if u.created_at and u.created_at >= cutoff_7d
)
```

### Pattern 4: usage_events Time-Window Query

**What:** PostgREST count query with `.gte("created_at", cutoff_iso)` for 7d/30d windows. All-time omits the filter.

**When to use:** Counting `message_sent` and `photo_generated` events per time window.

**Example:**
```python
# Source: Supabase PostgREST filter docs + existing pattern from billing.py queries
from datetime import datetime, timezone, timedelta

def _count_events(event_type: str, days: int | None) -> int:
    query = (
        supabase_admin.from_("usage_events")
        .select("id", count="exact")
        .eq("event_type", event_type)
    )
    if days is not None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query = query.gte("created_at", cutoff)
    result = query.execute()
    return result.count or 0
```

### Pattern 5: Frontend AdminRoute Guard

**What:** A route guard component that decodes the JWT to check `user_metadata.is_admin`. Redirects non-admins to `/chat` silently. Same client-side JWT decode pattern used in Phase 6 for `user_id` extraction.

**When to use:** Wrapping the `/admin` route in App.tsx.

**Example:**
```typescript
// Source: Consistent with ProtectedRoute + existing JWT atob pattern from Phase 6
function AdminRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)
  if (!token) return <Navigate to="/login" replace />

  // Decode JWT payload (middle segment) to read user_metadata
  // Same atob pattern established in Phase 6 for user_id extraction
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const isAdmin = payload?.user_metadata?.is_admin === true
    if (!isAdmin) return <Navigate to="/chat" replace />
  } catch {
    return <Navigate to="/chat" replace />
  }

  return <>{children}</>
}
```

### Anti-Patterns to Avoid

- **Polling usage_events for live data:** Manual refresh only — no `refetchInterval`. The dashboard is a batch-query view, not a live feed.
- **Exposing 403 error message to non-admins:** The frontend guard redirects silently to `/chat` before any API call is made. Never show "403 Forbidden" to regular users.
- **Querying auth.users with the anon client:** `auth.users` is only accessible via service role. Always use `supabase_admin.auth.admin.list_users()`.
- **Emitting usage events before the user action:** Always emit after — the user action must complete first. Fire-and-forget wrapping goes at the end of the handler.
- **Blocking on usage event write failure:** The `try/except` must never re-raise. Event write failures are a logging concern only.
- **Adding `require_admin` to `dependencies.py`:** Add it directly in `admin.py` router file — it's specific to admin context, not a global dependency.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accessing auth.users for active-user count | Custom SQL RPC function | `supabase_admin.auth.admin.list_users()` | Standard SDK method; SQL RPCs on auth schema require careful permissions |
| Time-window filtering | Python datetime math on raw rows | PostgREST `.gte("created_at", cutoff)` with `count="exact"` | Server-side counting avoids pulling all rows to Python |
| JWT admin check on frontend | Custom API endpoint to verify admin | Client-side `atob` JWT decode (established Phase 6 pattern) | No roundtrip needed; JWT already in store; matches project's existing decode pattern |
| Usage event helper module | Separate `services/usage.py` abstraction | Inline `try/except` at each emit point | Migration 005 already comments this pattern; 4 emit points don't justify an abstraction layer |

**Key insight:** The `supabase_admin` client already bypasses RLS — all admin reads are just standard PostgREST queries with the service role client that's already initialized in `database.py`.

---

## Common Pitfalls

### Pitfall 1: user_metadata vs app_metadata for Admin Check

**What goes wrong:** Reading `user.app_metadata.get("is_admin")` instead of `user.user_metadata.get("is_admin")`. The Supabase Dashboard "Edit User" UI exposes `user_metadata` under "User Metadata" — that's where the flag is set. `app_metadata` is a separate field.

**Why it happens:** The Supabase docs mention both fields. STATE.md is explicit: "Admin role assigned via Supabase user_metadata flag: `is_admin: true` (set manually in Supabase dashboard)."

**How to avoid:** Use `user.user_metadata or {}` in the backend dependency. In the frontend JWT decode, check `payload?.user_metadata?.is_admin`.

**Warning signs:** Admin user gets 403 even after setting the flag — wrong metadata field being checked.

---

### Pitfall 2: photo_generated Goes to audit_log, Not usage_events

**What goes wrong:** `photo_generated` is currently written to `audit_log` in `processor.py` (step 7 of the photo job). The `usage_events` table will have zero `photo_generated` rows even after deployment.

**Why it happens:** The audit_log write was the only instrumentation added during Phase 7. The `usage_events` table didn't exist until Phase 8.

**How to avoid:** In the emission wiring plan, add a separate `usage_events` insert for `photo_generated` in `processor.py` alongside the existing `audit_log` write. Do not replace the audit_log write — keep both.

**Warning signs:** ADMN-03 success criterion 3 fails: `usage_events` has zero `photo_generated` rows.

---

### Pitfall 3: subscription_created vs subscription_cancelled

**What goes wrong:** Phase 11 already emits a `subscription_cancelled` event in `billing.py`. The required event type for ADMN-02 is `subscription_created` (not `subscription_cancelled`). These are different events at different points in the webhook handler.

**Why it happens:** `subscription_cancelled` was added for survey tracking. `subscription_created` needs to be added in the `checkout.session.completed` branch of the webhook.

**How to avoid:** Add the `subscription_created` emit in `billing.py`'s `checkout.session.completed` handler, after `activate_subscription()` completes. The `user_id` is already extracted from `data.get("metadata", {}).get("user_id")` at that point.

**Warning signs:** `usage_events` table has `subscription_cancelled` rows but no `subscription_created` rows.

---

### Pitfall 4: supabase_admin.auth.admin.list_users() Pagination

**What goes wrong:** `list_users()` without pagination parameters returns up to 1000 users. If the app grows past 1000 users before Phase 12 is revisited, active-user counts will be silently capped.

**Why it happens:** The default `list_users()` call is paginated. At v1.1 launch scale this is a non-issue.

**How to avoid:** Add a comment noting the 1000-user pagination limit. At launch scale this is acceptable. Add `# TODO: paginate for >1000 users` comment for future awareness.

**Warning signs:** Active user count suspiciously rounds to 1000 when user base is larger.

---

### Pitfall 5: Frontend Route Guard Runs Before Token is Loaded

**What goes wrong:** On page refresh with a stored token, the `AdminRoute` guard runs synchronously before `useAuthStore` has hydrated from localStorage (Zustand persist middleware). The token is momentarily `null`, causing an immediate redirect to `/login`.

**Why it happens:** Zustand's `persist` middleware is synchronous in its hydration on initial render — but there's a brief tick before hydration completes in some configurations. `ProtectedRoute` already handles this same problem with a simple null check.

**How to avoid:** The existing `ProtectedRoute` pattern (`if (!token) return <Navigate to="/login" replace />`) is sufficient — Zustand `persist` hydrates synchronously before the first render in practice. Test by hard-refreshing on `/admin` while logged in as admin to verify no flash redirect occurs.

**Warning signs:** Admin user gets briefly redirected to /login on hard refresh.

---

### Pitfall 6: Mode Switch Emission Fires on "Already in this mode" Path

**What goes wrong:** Emitting `mode_switch` even when the user is already in the requested mode (the "already in mode" acknowledgement path). This inflates mode_switch counts.

**Why it happens:** The mode switch detection runs before checking if the target is the current mode. The SWITCH_TO_INTIMATE_MSG and SWITCH_TO_SECRETARY_MSG returns are the actual switches; the ALREADY_INTIMATE_MSG and ALREADY_SECRETARY_MSG returns are not switches.

**How to avoid:** Only emit `mode_switch` after `switch_mode()` is actually called — i.e., only on the successful mode change path, not the "already in this mode" path.

**Warning signs:** mode_switch count is much higher than expected relative to message_sent count.

---

## Code Examples

Verified patterns from project codebase:

### Existing Usage Event Emit Pattern (billing.py cancel endpoint)
```python
# Source: backend/app/routers/billing.py — cancel_subscription()
# This is the exact established pattern — replicate for all 4 emission points
try:
    supabase_admin.from_("usage_events").insert({
        "user_id": str(user.id),
        "event_type": "subscription_cancelled",
        "metadata": {"q1": body.q1, "q2": body.q2},
    }).execute()
except Exception as exc:
    logger.error("Failed to emit subscription_cancelled usage event: %s", exc)
```

### Supabase Active Subscriptions Count
```python
# Source: PostgREST count="exact" pattern
result = (
    supabase_admin.from_("subscriptions")
    .select("id", count="exact")
    .eq("status", "active")
    .execute()
)
active_subscriptions = result.count or 0
```

### Frontend Metrics Fetch Pattern (mirrors BillingPage.tsx)
```typescript
// Source: frontend/src/pages/BillingPage.tsx — useQuery pattern
const { data: metrics, isLoading } = useQuery({
  queryKey: ['admin-metrics'],
  queryFn: () => getAdminMetrics(token),
  staleTime: 0,  // Always fetch fresh on load (manual refresh)
  refetchOnWindowFocus: false,  // Manual refresh only
})
```

### Stat Card Component (using existing GlassCard)
```typescript
// Source: frontend/src/components/ui/GlassCard.tsx
// Each metric card follows BillingPage's GlassCard usage pattern
<GlassCard className="bg-white/5 border-white/10">
  <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-3">
    {metric.name}
  </h3>
  <div className="space-y-2">
    <MetricRow label="7d" value={metric.d7} />
    <MetricRow label="30d" value={metric.d30} />
    <MetricRow label="All time" value={metric.all} />
  </div>
</GlassCard>
```

### usage_events Table Schema (already live)
```sql
-- Source: backend/migrations/005_usage_events.sql
CREATE TABLE IF NOT EXISTS public.usage_events (
  id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     UUID        REFERENCES auth.users(id) ON DELETE SET NULL,
  event_type  TEXT        NOT NULL,
  -- Expected: 'message_sent' | 'photo_generated' | 'mode_switch' | 'subscription_created'
  metadata    JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- RLS enabled. Admin reads via service role only (supabase_admin).
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Supabase custom JWT claims for roles | user_metadata flag (`is_admin: true`) | v1.1 roadmap decision | Simpler to set manually in Dashboard; no RLS policy changes needed |
| Separate `services/usage.py` helper | Inline try/except at each emit point | STATE.md comments | Migration 005 anticipated this; inline is appropriate at 4 emission points |

**No deprecated approaches in this phase.** All patterns are consistent with Phases 8–11.

---

## Open Questions

1. **supabase_admin.auth.admin.list_users() Python SDK method availability**
   - What we know: The `supabase-py` SDK has an `auth.admin` namespace with `list_users()` since v2. The project uses supabase-py (version visible in requirements.txt not checked here).
   - What's unclear: The exact method signature and return type in the installed version.
   - Recommendation: In Plan 1, verify the method works in a test call before building the full endpoint. Fallback: use `supabase_admin.rpc("get_active_users")` with a custom SQL function if `list_users()` is unavailable.

2. **Frontend JWT decode field path for is_admin**
   - What we know: Supabase JWTs include `user_metadata` in the payload. The Phase 6 decision used `atob` on the middle segment to extract `sub` as `user_id`.
   - What's unclear: Whether Supabase includes `user_metadata` in the JWT payload or only in the `get_user()` response.
   - Recommendation: In Plan 3, test the JWT payload contents by decoding in browser console. Fallback: call `GET /admin/me` (a lightweight backend endpoint that reads user_metadata and returns `{is_admin: bool}`) if `user_metadata` is not in the JWT.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (frontend) | Vitest ^4.0.18 + @testing-library/react |
| Framework (backend) | pytest (existing test suite) |
| Config file (frontend) | `frontend/vitest.config.ts` |
| Config file (backend) | none — run from `backend/` directory |
| Quick run command (frontend) | `cd frontend && npx vitest run --reporter=verbose` |
| Quick run command (backend) | `cd backend && python -m pytest tests/ -x -q` |
| Full suite command | `cd frontend && npx vitest run && cd ../backend && python -m pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADMN-01 | GET /admin/metrics returns 5 metrics with 3 time windows | manual-only (requires live Supabase data) | N/A — verify manually by visiting /admin | N/A |
| ADMN-01 | AdminPage renders 5 stat cards with correct labels | unit | `cd frontend && npx vitest run --reporter=verbose src/pages/AdminPage.test.tsx` | ❌ Wave 0 |
| ADMN-02 | usage_events receives message_sent after chat | manual-only (requires live DB write) | N/A — verify via Supabase Dashboard | N/A |
| ADMN-02 | emit_* functions called on correct code paths | unit (backend mock) | `cd backend && python -m pytest tests/test_admin_events.py -x -q` | ❌ Wave 0 |
| ADMN-03 | require_admin raises 403 for non-admin user | unit | `cd backend && python -m pytest tests/test_admin_access.py -x -q` | ❌ Wave 0 |
| ADMN-03 | AdminRoute redirects non-admin to /chat | unit | `cd frontend && npx vitest run --reporter=verbose src/pages/AdminPage.test.tsx` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npx vitest run --reporter=verbose`
- **Per wave merge:** Full suite: `cd frontend && npx vitest run && cd ../backend && python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/src/pages/AdminPage.test.tsx` — covers ADMN-01 (card rendering) + ADMN-03 (AdminRoute redirect)
- [ ] `backend/tests/test_admin_access.py` — covers ADMN-03 (require_admin dependency: 403 for non-admin, 200 for admin)
- [ ] `backend/tests/test_admin_events.py` — covers ADMN-02 (usage event emit points wired correctly, mocked supabase_admin)

---

## Sources

### Primary (HIGH confidence)
- Project codebase `backend/app/routers/billing.py` — existing usage_events emit pattern (fire-and-forget try/except block)
- Project codebase `backend/app/dependencies.py` — `get_current_user` pattern extended by `require_admin`
- Project codebase `backend/app/database.py` — `supabase_admin` service role client
- Project codebase `backend/migrations/005_usage_events.sql` — table schema, RLS, indexes
- Project codebase `backend/app/services/chat.py` — mode switch + message flow (emission points identified)
- Project codebase `backend/app/services/jobs/processor.py` — photo_generated currently going to audit_log
- Project codebase `frontend/src/App.tsx` — route guard patterns (ProtectedRoute, OnboardingGate)
- Project codebase `frontend/src/components/ui/GlassCard.tsx` — GlassCard component interface
- Project codebase `frontend/vitest.config.ts` — test infrastructure (jsdom, globals, setupFiles)
- `.planning/phases/12-admin-dashboard/12-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- `STATE.md` v1.1 roadmap decision: "Admin dashboard protected by require_admin dependency reading app_metadata.role == 'admin' from JWT" — note: this references app_metadata, but CONTEXT.md explicitly says user_metadata. CONTEXT.md takes precedence as the most recent locked decision.
- `STATE.md` Phase 8 decision: "usage_events RLS enabled with no user SELECT policy — admin reads via service role key only" — confirms supabase_admin is required for all admin queries

### Tertiary (LOW confidence)
- `supabase_admin.auth.admin.list_users()` method availability — assumed from supabase-py v2 SDK documentation, not verified against installed version in requirements.txt

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all patterns verified in existing codebase
- Architecture: HIGH — all patterns derived directly from existing routers and components
- Pitfalls: HIGH — pitfalls 1, 2, 3 identified from direct codebase inspection; pitfalls 4, 5, 6 from known FastAPI/Zustand/Supabase behavior

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable stack — 30-day window)
