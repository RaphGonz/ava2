# Phase 4: Secretary Skills - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can manage Google Calendar and ask research questions via WhatsApp chat. The bot acts as an efficient personal assistant: adding/viewing meetings, setting reminders (stored for delivery), and answering factual research questions. Chat-based interaction only — no UI dashboard, no autonomous scheduling, no voice. New capabilities (advanced reminders delivery, notifications system) belong in future phases.

</domain>

<decisions>
## Implementation Decisions

### Confirmation & Response Style

- After adding a meeting: structured summary format — "Added: [Title] · [Day] · [Time]"
- Schedule display: one event per line with bullet points — "• Tue 3pm — Team standup"
- Tone: efficient assistant — crisp, no filler words, no emojis, gets to the point
- Reminders: single daily digest (e.g., morning summary of the day's events) OR a session-start reminder — NOT per-meeting pings throughout the day; frequency should respect user preference (some users are busy and don't need reminders, others have sparse schedules and do)

### Research Response Format

- Length: one sharp paragraph, 3–5 sentences max — covers the core answer concisely
- Sources: one source link appended at the end ("Source: [url]")
- Broad/ambiguous questions: ask one clarifying question before answering ("That's a big topic — are you thinking about X, Y, or Z?")
- Follow-up offers: none — give the answer and stop; user asks if they want more

### Conflict & Error Handling

- Calendar conflict: warn and ask — "You already have [X] at that time. Add anyway?" — user confirms before overwriting
- Calendar API / auth error: plain error message — "Couldn't connect to Google Calendar. Check your account settings." — no retries, no technical details
- Research with no solid results: best-effort answer with caveat — "I'm not fully certain, but..." — never hard-refuse if something useful can be said
- Ambiguous intent (can't tell if user wants calendar, research, or general chat): ask one disambiguation question — "Did you want me to add that to your calendar, or look it up?"

### Natural Language Parsing

- Date/time parsing: very flexible — "mardi à 3h", "next Tuesday at 3", "tomorrow morning", "in 2 hours" all work; bot infers as much as it can from context
- Missing required field (e.g., meeting with no time): ask for the single missing piece — "When should I schedule that?" — one follow-up per gap, not a form
- Intent detection: LLM intent classification — AI call classifies each message as calendar, research, or general chat before routing; handles nuanced and indirect phrasing better than keyword matching
- Time zone: single configured timezone per user stored in their profile; all calendar operations use it — no per-message timezone handling

### Claude's Discretion

- Exact wording of error messages (keep them practical and non-technical)
- Skill registry architecture / plugin pattern for adding new skills
- How to handle edge cases in date parsing (e.g., "next month" with no day)
- Reminder storage format and delivery scheduling mechanics

</decisions>

<specifics>
## Specific Ideas

- Reminders philosophy: the user doesn't want WhatsApp spam throughout the day. A morning digest or session-start briefing is the right model — like an EA reading out the day's agenda, not a notification system pinging every event
- This is a bilingual bot (French + English) — date/time parsing must handle both languages naturally
- The skill registry must be modular enough that new skills (e.g., a future "Spotify" skill) can be added as plugins without rewriting routing logic

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-secretary-skills*
*Context gathered: 2026-02-24*
