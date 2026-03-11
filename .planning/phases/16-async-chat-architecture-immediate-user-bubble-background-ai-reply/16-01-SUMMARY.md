---
phase: 16-async-chat-architecture-immediate-user-bubble-background-ai-reply
plan: "01"
subsystem: chat
tags: [async, chat, fastapi, react-query, ux]
dependency_graph:
  requires: []
  provides: [CHAT-01, CHAT-02, CHAT-03]
  affects: [backend/app/routers/web_chat.py, frontend/src/api/chat.ts]
tech_stack:
  added: []
  patterns:
    - asyncio.ensure_future for fire-and-forget coroutines immune to CORSMiddleware cancellation
    - React Query setQueryData append in onSuccess (no optimistic onMutate, no invalidateQueries)
key_files:
  created: []
  modified:
    - backend/app/routers/web_chat.py
    - frontend/src/api/chat.ts
decisions:
  - "asyncio.ensure_future (not BackgroundTasks) for LLM task — CORSMiddleware cancels BackgroundTasks on connection close (confirmed Phase 07 pattern)"
  - "onSuccess setQueryData append (not onMutate) — server returns real user row immediately; optimistic id causes duplicate bubble"
  - "No invalidateQueries in onSuccess — full refetch before assistant reply lands defeats the purpose; 3s poll handles assistant row naturally"
  - "GET /chat/history unchanged — polling at 3s is the honest mechanism for assistant reply delivery"
metrics:
  duration_minutes: 9
  completed_date: "2026-03-11"
  tasks_completed: 2
  files_modified: 2
---

# Phase 16 Plan 01: Async Chat Architecture — Immediate User Bubble + Background AI Reply Summary

**One-liner:** Synchronous user-message DB insert + asyncio.ensure_future LLM task eliminates flash-disappear bug by returning the real user row instantly for React Query cache append.

## What Was Built

Refactored the web chat message flow across two files:

**Backend (`web_chat.py`):**
- Added `import asyncio`
- Extracted `_run_llm_and_insert` coroutine: NormalizedMessage construction, `_web_adapter.receive()` LLM call, assistant row insert — all wrapped in `except Exception` with `logger.error` so it never propagates to the event loop
- Rewrote `send_message` handler: fetch avatar first, insert user row synchronously via `supabase_admin`, fire `asyncio.ensure_future(_run_llm_and_insert(...))`, return `{id, role, content, created_at}` from the inserted row
- Removed the two-row batch insert (`[user_row, assistant_row]`)
- GET /chat/history and `_rewrite_photo_paths` are unchanged

**Frontend (`chat.ts`):**
- Removed `onMutate` callback entirely (was creating optimistic temp-id bubble)
- Removed `invalidateQueries` from `onSuccess`
- Added `onSuccess(userMessage: ChatMessage)` that calls `queryClient.setQueryData` to append the real server-returned row
- Changed `mutationFn` return type annotation from `Promise<{ reply: string }>` to `Promise<ChatMessage>`
- `useChatHistory`, `ChatMessage`, `ApiError`, `UseSendMessageOptions` — all unchanged
- `refetchInterval: 3000` polling continues unchanged — picks up assistant reply when background task completes

## Root Cause Fixed

The old flow: POST /chat → await LLM (~2-10s) → batch insert both rows → return `{reply}`. Frontend used `onMutate` to show an optimistic user bubble (temp id), but the 3s poll fired before the DB contained the user row, so the poll returned no user message, destroying the optimistic bubble. It reappeared when the LLM finally finished. This caused the flash-disappear-reappear bug.

The new flow: POST /chat → insert user row (~10ms) → `ensure_future` LLM task → return user row. Frontend appends the real row to cache in `onSuccess`. No fake ids, no flash, no duplicates.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | bbfde00 | feat(16-01): refactor POST /chat — synchronous user insert + asyncio.ensure_future LLM task |
| Task 2 | f6bac64 | feat(16-01): remove onMutate, add onSuccess setQueryData append in useSendMessage |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- backend/app/routers/web_chat.py: FOUND
- frontend/src/api/chat.ts: FOUND
- 16-01-SUMMARY.md: FOUND
- commit bbfde00: FOUND (Task 1 — backend refactor)
- commit f6bac64: FOUND (Task 2 — frontend refactor)
