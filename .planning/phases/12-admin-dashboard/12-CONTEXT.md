# Phase 12: Admin Dashboard - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

A protected `/admin` page for operators to view 5 product health metrics. Regular users are blocked and redirected. The `usage_events` table (created in Phase 8) needs emission points wired across the codebase. No new capabilities — reporting and access control only.

</domain>

<decisions>
## Implementation Decisions

### Metrics displayed
- 5 metrics: active users, messages sent, photos generated, active subscriptions, new signups
- Each metric shows three time windows side by side: 7d / 30d / all-time
- Data sources (mixed, not all from usage_events):
  - Active users (7d): auth.users last_sign_in_at
  - New signups: auth.users created_at
  - Active subscriptions: subscriptions table
  - Messages sent: usage_events (message_sent)
  - Photos generated: usage_events (photo_generated)
- Manual refresh only — no auto-refresh or polling

### Access control
- Non-admin navigating to /admin: silent redirect to /chat (no error message shown)
- Admin role assigned via Supabase user_metadata flag: `is_admin: true` (set manually in Supabase dashboard)
- Enforcement at both layers: backend API returns 403, frontend route guard redirects non-admins
- No visible link to /admin anywhere in the UI — URL-only access for operators

### Usage event wiring
- 4 required event types: `message_sent`, `photo_generated`, `mode_switch`, `subscription_created`
- Emission strategy: fire-and-forget, silent failure (event write errors are logged but never block the user action)
- Each event row includes `user_id` for future per-user analysis
- `usage_events` table already exists in production (created in Phase 8 migration) — wire emission points only, no schema changes needed

### Dashboard layout
- Stat cards grid — one card per metric, 5 cards total
- Each card displays the metric name and 7d / 30d / all-time values
- Page header: "Admin Dashboard" title + last-updated timestamp showing data freshness
- Style matches existing app (Tailwind, dark theme, existing card/component patterns)

### Claude's Discretion
- Card grid column count / responsive breakpoints
- Exact Tailwind classes and color choices within existing palette
- Loading state while metrics fetch
- Error state if the metrics query fails

</decisions>

<specifics>
## Specific Ideas

- Card layout visual reference: each card shows metric name + three labeled rows (7d / 30d / All)
- "Last updated: HH:MM" timestamp in the header so operator knows data freshness
- No design investment needed beyond matching existing app style

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-admin-dashboard*
*Context gathered: 2026-03-10*
