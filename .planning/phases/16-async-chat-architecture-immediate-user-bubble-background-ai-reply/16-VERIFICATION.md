---
phase: 16-async-chat-architecture-immediate-user-bubble-background-ai-reply
verified: 2026-03-11T00:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 16: Async Chat Architecture — Immediate User Bubble + Background AI Reply

**Phase Goal:** Fix the web chat message flow so the user's message appears in the thread immediately upon send, and the AI reply appears independently when ready — without optimistic hacks. POST /chat writes the user message to DB and returns it instantly; the LLM runs via asyncio.ensure_future; GET /chat/history polling picks up the AI reply when it lands.
**Verified:** 2026-03-11
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User's message bubble appears in the chat thread immediately after hitting send — no waiting for the AI | VERIFIED | `send_message` inserts user row synchronously and returns `{id, role, content, created_at}` before the LLM starts; `onSuccess` in `chat.ts` appends this real row to `['chat-history']` cache immediately |
| 2 | The AI reply appears independently in the thread ~2-10s later when the background task completes | VERIFIED | `asyncio.ensure_future(_run_llm_and_insert(...))` fires after the user insert; the coroutine inserts the assistant row into `messages`; `refetchInterval: 3000` poll in `useChatHistory` picks it up |
| 3 | No bubble flash: user bubble does not disappear and reappear during the 3s poll cycle | VERIFIED | Root cause eliminated — user row is in DB before `send_message` returns, so the 3s poll always finds it; no mismatch between optimistic state and DB state |
| 4 | No duplicate bubble: user message appears exactly once in the thread | VERIFIED | `onMutate` is absent from `useSendMessage`; only `onSuccess` touches the cache; no temp-id race with real-id |
| 5 | POST /chat returns the user message row `{id, role, content, created_at}` — not `{reply: string}` | VERIFIED | `web_chat.py` lines 99–103 return `{"id": user_row["id"], "role": user_row["role"], "content": user_row["content"], "created_at": user_row["created_at"]}`; `mutationFn` in `chat.ts` typed as `Promise<ChatMessage>` |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/routers/web_chat.py` | Async POST /chat — synchronous user-message insert, asyncio.ensure_future LLM task | VERIFIED | File exists, 189 lines, substantive. Contains `asyncio.ensure_future`, `_run_llm_and_insert` coroutine with `except Exception` guard, `send_message` handler returning real user row. Python syntax check: OK. |
| `frontend/src/api/chat.ts` | useSendMessage — onSuccess setQueryData append, no onMutate | VERIFIED | File exists, 72 lines, substantive. Exports `useSendMessage`, `useChatHistory`, `ChatMessage`, `ApiError`. `onMutate` absent. `onSuccess` calls `queryClient.setQueryData`. `invalidateQueries` absent from `useSendMessage`. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/routers/web_chat.py` | supabase messages table | synchronous insert before response | WIRED | `supabase_admin.from_("messages").insert({...role": "user"...}).execute()` at lines 79–85; result checked with `if not result.data`; `user_row = result.data[0]` |
| `backend/app/routers/web_chat.py` | `_run_llm_and_insert` coroutine | asyncio.ensure_future | WIRED | `asyncio.ensure_future(_run_llm_and_insert(user_id, body.text, avatar))` at line 96 — exact pattern required by plan |
| `frontend/src/api/chat.ts` | `['chat-history']` React Query cache | queryClient.setQueryData in onSuccess | WIRED | `queryClient.setQueryData<ChatMessage[]>(['chat-history'], prev => [...(prev ?? []), userMessage])` at lines 64–67 |

---

### Requirements Coverage

The PLAN frontmatter declares CHAT-01, CHAT-02, CHAT-03. These identifiers are defined locally in the phase RESEARCH.md as phase-specific requirement labels, not entries in the v1.1 `.planning/REQUIREMENTS.md` (which covers INFRA/EMAI/AUTH/LAND/SUBS/ADMN scopes only). The ROADMAP.md phase 16 entry (`**Requirements**: CHAT-01, CHAT-02, CHAT-03`) is the authoritative reference for these IDs in this context.

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CHAT-01 | 16-01-PLAN.md | POST /chat inserts user message into DB immediately and returns user message row (id, role, content, created_at) — not the AI reply | SATISFIED | `send_message` inserts user row synchronously, checks `result.data`, returns `{id, role, content, created_at}` from `user_row`. Old `{reply: string}` return shape is gone. |
| CHAT-02 | 16-01-PLAN.md | AI reply is generated in a background task and inserted into DB when ready — polling picks it up on the next cycle | SATISFIED | `_run_llm_and_insert` coroutine calls `_web_adapter.receive(msg)` then inserts assistant row; scheduled via `asyncio.ensure_future()` — immune to CORSMiddleware cancellation. `refetchInterval: 3000` in `useChatHistory` unchanged. |
| CHAT-03 | 16-01-PLAN.md | Frontend displays user bubble immediately on send (from onSuccess, not onMutate) and AI reply appears when poll retrieves it — no optimistic hack | SATISFIED | `onMutate` absent from `useSendMessage`; `onSuccess(userMessage: ChatMessage)` appends real row to `['chat-history']` cache via `setQueryData`; `invalidateQueries` absent. |

**Note on REQUIREMENTS.md orphan check:** CHAT-01/02/03 do not appear in `.planning/REQUIREMENTS.md` (the v1.1 launch-ready requirements doc). The same IDs exist in the v1.0 milestone REQUIREMENTS but with different definitions (text-conversation capability, session memory, mode switching) — those were closed in Phase 3. The Phase 16 CHAT-01/02/03 are scoped to this phase only and are fully documented in ROADMAP.md and RESEARCH.md. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/routers/web_chat.py` | 88–89 | `from fastapi import HTTPException` inside function body | Info | Not a functional issue — HTTPException is already available from the outer import scope via FastAPI, but a local import works fine. No impact. |

No blocker or warning anti-patterns found. No TODOs, FIXMEs, placeholders, or stub implementations detected. The `except Exception` guard in `_run_llm_and_insert` is correct (does not catch `BaseException`/`CancelledError`), matching the RESEARCH.md guidance.

---

### Human Verification Required

All automated checks pass. The following behaviors need human observation to confirm end-to-end UX:

#### 1. No-flash send verification

**Test:** Open the web chat in a browser. Send a message. Observe the chat thread.
**Expected:** User bubble appears immediately after pressing send (sub-100ms), stays visible throughout the full 3s poll cycle, and never disappears.
**Why human:** Cannot verify absence-of-flash from static code analysis — requires live browser observation with the 3s poll running.

#### 2. AI reply delivery via polling

**Test:** After sending a message, wait 3–15 seconds.
**Expected:** AI reply bubble appears without any page action, delivered by the 3s refetch.
**Why human:** Requires live LLM call and DB write from the background task — cannot simulate with static analysis.

#### 3. No duplicate user bubble

**Test:** Send a message and observe the thread for ~10 seconds.
**Expected:** User message appears exactly once. It does not appear a second time on the next poll.
**Why human:** Duplicate detection requires observing React Query cache reconciliation behavior in a live browser.

---

### Gaps Summary

No gaps. All five must-have truths are verified, both artifacts are substantive and wired, all three key links confirmed, and all three phase-scoped requirements are satisfied. The implementation matches the plan exactly — no deviations were documented in SUMMARY.md and no contradictions were found in the code.

Commits `bbfde00` and `f6bac64` are confirmed present in git history.

---

_Verified: 2026-03-11_
_Verifier: Claude (gsd-verifier)_
