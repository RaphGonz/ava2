---
phase: 06-web-app-multi-platform
plan: 03
subsystem: api
tags: [python, fastapi, protocol, structural-typing, platform-adapter, whatsapp, webhook]

# Dependency graph
requires:
  - phase: 06-01
    provides: DB schema with user_preferences.preferred_platform column
  - phase: 03-core-intelligence-mode-switching
    provides: ChatService.handle_message() orchestrator
  - phase: 02-infrastructure-user-management
    provides: supabase_admin, user_lookup, whatsapp send helper
provides:
  - PlatformAdapter Protocol (runtime_checkable) + NormalizedMessage dataclass
  - WhatsAppAdapter — wraps webhook receive/send logic, routes via platform_router
  - WebAdapter — HTTP-originated messages adapter with no-op send()
  - platform_router.route() — single enforcement point for preferred_platform
  - webhook.py refactored to use _whatsapp_adapter singleton
affects:
  - 06-04 (web chat router uses WebAdapter)
  - any future platform adapter (Telegram, SMS, etc.)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Structural Protocol typing: PlatformAdapter mirrors LLMProvider pattern from Phase 3 — isinstance() check without inheritance"
    - "Module-level singleton pattern extended: _whatsapp_adapter added alongside _chat_service in webhook.py"
    - "Adapter transport/logic separation: adapters handle delivery only, all business logic stays in ChatService"
    - "preferred_platform enforcement in single router function, not duplicated per adapter"

key-files:
  created:
    - backend/app/adapters/__init__.py
    - backend/app/adapters/base.py
    - backend/app/adapters/whatsapp_adapter.py
    - backend/app/adapters/web_adapter.py
    - backend/app/services/platform_router.py
  modified:
    - backend/app/routers/webhook.py

key-decisions:
  - "PlatformAdapter uses Python Protocol (structural typing) — any class with async receive() and send() qualifies without inheritance, mirroring LLMProvider pattern from Phase 3"
  - "platform_router.py uses supabase_admin for preferred_platform lookup — webhook context has no user JWT, same rationale as Phase 2 decision"
  - "WhatsAppAdapter.send() resolves user_id to phone internally via supabase_admin — decouples webhook.py from knowing the sender phone at send time"
  - "WebAdapter.send() is intentional no-op — web replies returned synchronously in HTTP response body, no async push needed"
  - "preferred_platform enforcement lives in platform_router.route(), not per-adapter — avoids duplication per research anti-patterns"

patterns-established:
  - "Adapter pattern: new platforms need only one class with receive()/send() — zero changes to ChatService or core pipeline"
  - "NormalizedMessage envelope: all platform metadata stripped, core pipeline sees user_id/text/platform/timestamp only"
  - "In-character redirect template for platform mismatch — warm tone, no error framing"

requirements-completed: [PLAT-05, PLAT-04]

# Metrics
duration: 9min
completed: 2026-02-24
---

# Phase 6 Plan 03: Platform Adapter Layer Summary

**PlatformAdapter Protocol + NormalizedMessage + WhatsAppAdapter + WebAdapter + platform_router with preferred_platform enforcement, webhook.py refactored to adapter pattern**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-24T16:40:05Z
- **Completed:** 2026-02-24T16:49:11Z
- **Tasks:** 2 completed
- **Files modified:** 6

## Accomplishments
- Created `backend/app/adapters/` package with PlatformAdapter Protocol (runtime_checkable) and NormalizedMessage dataclass, mirroring the LLMProvider structural typing pattern from Phase 3
- Implemented platform_router.route() as the single enforcement point for preferred_platform — checks via supabase_admin, returns in-character redirect on mismatch, dispatches to ChatService.handle_message() on match
- Built WhatsAppAdapter (wraps existing webhook logic) and WebAdapter (no-op send for HTTP responses); both pass isinstance(x, PlatformAdapter) structural check at runtime
- Refactored webhook.py to use _whatsapp_adapter singleton — removed direct ChatService calls from webhook, now routes through platform_router transparently
- All 47 existing tests continue to pass

## Task Commits

Each task was committed atomically:

1. **Task 1: PlatformAdapter Protocol, NormalizedMessage, and platform_router** - `bd4495f` (feat)
2. **Task 2: WhatsApp and Web adapters, webhook.py refactor** - `38dd669` (feat)

## Files Created/Modified
- `backend/app/adapters/__init__.py` — Empty package init (creates the adapters package)
- `backend/app/adapters/base.py` — PlatformAdapter Protocol (runtime_checkable) + NormalizedMessage dataclass
- `backend/app/adapters/whatsapp_adapter.py` — Concrete WhatsApp adapter; receive() -> platform_router; send() resolves user_id to phone via supabase_admin
- `backend/app/adapters/web_adapter.py` — Concrete Web adapter; receive() -> platform_router; send() is no-op
- `backend/app/services/platform_router.py` — route() function: preferred_platform check + ChatService dispatch
- `backend/app/routers/webhook.py` — Refactored to use _whatsapp_adapter singleton; removed direct ChatService calls

## How the Protocol Structural Check Works

`PlatformAdapter` is decorated with `@runtime_checkable` from `typing`. This enables `isinstance(obj, PlatformAdapter)` checks at runtime without requiring `obj`'s class to inherit from `PlatformAdapter`.

Python checks structurally: does the object have `receive` and `send` as callable attributes? Both `WhatsAppAdapter` and `WebAdapter` implement these methods, so `isinstance(wa, PlatformAdapter)` returns `True` even though neither class imports or subclasses `PlatformAdapter`.

This is the same pattern used by `LLMProvider` in `backend/app/services/llm/base.py` (Phase 3).

## platform_router.route() Signature

```python
async def route(
    chat_service: ChatService,
    user_id: str,
    incoming_platform: str,   # "whatsapp" | "web"
    message: NormalizedMessage,
    avatar: dict | None,
) -> str:
```

Returns in-character redirect string if `preferred_platform` is set and doesn't match `incoming_platform`. Otherwise delegates to `chat_service.handle_message()`.

## Decisions Made
- PlatformAdapter uses structural typing (Protocol) not ABC — consistent with LLMProvider established in Phase 3
- platform_router uses supabase_admin for preferred_platform lookup — webhook context has no user JWT (same rationale as Phase 2 phone lookup)
- WhatsAppAdapter.send() resolves user_id to phone internally — decouples webhook.py from sender phone at reply time
- WebAdapter.send() is intentional no-op — HTTP replies return synchronously, no push mechanism needed
- preferred_platform enforcement is centralized in platform_router — not duplicated per adapter

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. New environment variables or dashboard steps were not introduced in this plan.

## Next Phase Readiness

- Platform adapter layer complete — WebAdapter is ready to be wired into the web_chat.py router (Plan 06-04)
- Adding a new platform (Telegram, SMS) requires only: one new adapter class + one singleton in its router
- No changes to ChatService, platform_router, or existing adapters needed for new platforms

## Self-Check: PASSED

All created files verified present on disk. Both task commits verified in git log.

- FOUND: backend/app/adapters/__init__.py
- FOUND: backend/app/adapters/base.py
- FOUND: backend/app/adapters/whatsapp_adapter.py
- FOUND: backend/app/adapters/web_adapter.py
- FOUND: backend/app/services/platform_router.py
- FOUND: backend/app/routers/webhook.py (modified)
- FOUND: .planning/phases/06-web-app-multi-platform/06-03-SUMMARY.md
- FOUND commit: bd4495f (Task 1)
- FOUND commit: 38dd669 (Task 2)

---
*Phase: 06-web-app-multi-platform*
*Completed: 2026-02-24*
