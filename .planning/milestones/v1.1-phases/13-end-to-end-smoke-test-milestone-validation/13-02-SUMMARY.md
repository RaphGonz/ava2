---
phase: 13-end-to-end-smoke-test-milestone-validation
plan: "02"
subsystem: validation
tags: [smoke-test, milestone, production, validation]
dependency_graph:
  requires: [13-01]
  provides: [v1.1-milestone-shipped]
  affects: [docs/smoke-test-runbook.md, .planning/ROADMAP.md, .planning/STATE.md]
tech_stack:
  added: []
  patterns:
    - In-memory signed URL cache with TTL to prevent polling flicker
    - [PHOTO]url[/PHOTO] token parsed and rendered as <img> in ChatBubble
key_files:
  created: []
  modified:
    - docs/smoke-test-runbook.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - frontend/src/components/ChatBubble.tsx
    - backend/app/routers/web_chat.py
---

## What Was Built

Executed the full Phase 13 smoke test runbook against https://avasecret.org. All 28 v1.1 success criteria PASS. The v1.1 Launch Ready milestone is declared **SHIPPED**.

## Automated Tests

All pytest smoke tests PASS:
- `test_smoke_paywall.py`: 3/3 (401 no-auth, 402 unsubscribed, 403 non-admin)
- `test_smoke_usage_events.py`: 1/1 (all 4 event types: message_sent, photo_generated, mode_switch, subscription_created)

## Bugs Found and Fixed During Validation

### Bug 1: Photo rendered as raw URL text (SC-4)
- **Symptom**: `[PHOTO]https://...signed-url...[/PHOTO]` displayed as plain text in chat
- **Root cause**: `ChatBubble.tsx` rendered `content` directly with no token parsing
- **Fix**: Added `renderContent()` that detects `[PHOTO]url[/PHOTO]` and renders `<img>` tag
- **Commit**: 9c86a54

### Bug 2: Signed URL changing every 3 seconds (flicker)
- **Symptom**: Image URL text changed visibly on every 3s poll (and would cause img reload)
- **Root cause**: `_rewrite_photo_paths()` generated a new signed URL on every `GET /chat/history` call
- **Fix**: Added `_signed_url_cache` dict; URLs reused for ~50 min, regenerated only when <10 min TTL remains
- **Commit**: 9162b54

## Self-Check: PASSED

All 28 evidence table rows: PASS
ROADMAP.md Phase 13: marked complete
STATE.md: updated to v1.1 SHIPPED
