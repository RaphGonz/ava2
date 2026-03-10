# Requirements: Ava — v1.1 Launch Ready

**Defined:** 2026-03-02
**Core Value:** A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app or web app the user already uses.

## v1.1 Requirements

Requirements for the Launch Ready milestone. Each maps to roadmap phases (starting at Phase 8).

### Infrastructure & Deployment

- [x] **INFRA-01**: App is deployed to a production VPS (Hetzner/DigitalOcean) and running
- [x] **INFRA-02**: All traffic is served over HTTPS with automatic certificate renewal (Caddy)
- [x] **INFRA-03**: Firewall configured — only ports 80 and 443 exposed publicly
- [x] **INFRA-04**: All production API credentials wired and verified (WhatsApp, ComfyUI Cloud, Stripe, OpenAI, Tavily, Supabase)

### Email

- [x] **EMAI-01**: Email DNS records (SPF/DKIM/DMARC) configured on sending domain for inbox deliverability
- [x] **EMAI-02**: User receives a welcome email after signing up
- [x] **EMAI-03**: User receives a receipt email after a successful subscription payment
- [x] **EMAI-04**: User receives a confirmation email after cancelling their subscription

### Auth Polish

- [x] **AUTH-01**: User can sign in and sign up with Google (one-click OAuth via Supabase)
- [x] **AUTH-02**: User can reset a forgotten password via an email link

### Landing Page

- [x] **LAND-01**: Visitor lands on a designed page with hero section, features section, and pricing (Figma design provided at build time)
- [x] **LAND-02**: Visitor can click a CTA button and reach the sign-up flow directly
- [x] **LAND-03**: Landing page copy frames Ava as an AI companion/assistant (Stripe-compliant — no explicit NSFW framing on public surfaces)

### Subscription Management

- [x] **SUBS-01**: User can view their current plan name, status, and next billing date
- [x] **SUBS-02**: User can access invoice history and update payment method (redirects to Stripe Customer Portal)
- [x] **SUBS-03**: User can cancel their subscription from the settings/billing page
- [x] **SUBS-04**: Cancellation flow shows an exit survey before confirming (what they liked, what they'd add, why they're leaving)
- [x] **SUBS-05**: Cancellation is non-coercive: survey is skippable, ≤ 3 clicks to complete, access retained until period end (`cancel_at_period_end=True`)

### Admin Dashboard

- [ ] **ADMN-01**: Operator can view key metrics: active users (7-day), messages sent, photos generated, active subscriptions, new signups
- [x] **ADMN-02**: Usage events are logged to a `usage_events` table (message_sent, photo_generated, mode_switch, subscription_created)
- [ ] **ADMN-03**: `/admin` route is restricted to admin role only — regular users receive 403

## Deferred to v1.2+

Features acknowledged but not in scope for this milestone.

### Growth & Engagement

- **MEMR-01**: Bot remembers user preferences and past conversations across sessions (long-term memory)
- **SKIL-02**: Reminder system — user can set time-based reminders via chat
- **ESCL-01**: Photo escalation from mild to explicit based on conversation context (currently static per spiciness_level)

### Platforms

- **MPLAT-01**: Telegram adapter
- **MPLAT-02**: Facebook Messenger adapter

### Content & Personas

- **PERS-02**: Expanded persona library (10+ personalities)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full marketing site (multi-page) | Landing page SPA route is sufficient for v1.1 launch |
| User-facing usage stats | Admin-only dashboard is sufficient; user stats deferred |
| In-app churn retention offer (discount) | Too complex for v1.1; operator reviews survey responses manually |
| Real-time analytics / live dashboard | Batch queries on usage_events table are sufficient at current scale |
| Multi-language support | English only — demand-driven post-launch |
| Native mobile app | WhatsApp + web app are the interfaces |
| Self-hosted option | Cloud only |
| Video/voice | Deferred to v2 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 8 | Complete |
| INFRA-02 | Phase 8 | Complete |
| INFRA-03 | Phase 8 | Complete |
| INFRA-04 | Phase 8 | Complete |
| EMAI-01 | Phase 8 | Complete |
| EMAI-02 | Phase 9 | Complete |
| EMAI-03 | Phase 9 | Complete |
| EMAI-04 | Phase 9 | Complete |
| AUTH-01 | Phase 9 | Complete |
| AUTH-02 | Phase 9 | Complete |
| LAND-01 | Phase 10 | Complete |
| LAND-02 | Phase 10 | Complete |
| LAND-03 | Phase 10 | Complete |
| SUBS-01 | Phase 11 | Complete |
| SUBS-02 | Phase 11 | Complete |
| SUBS-03 | Phase 11 | Complete |
| SUBS-04 | Phase 11 | Complete |
| SUBS-05 | Phase 11 | Complete |
| ADMN-01 | Phase 12 | Pending |
| ADMN-02 | Phase 12 | Complete |
| ADMN-03 | Phase 12 | Pending |

**Coverage:**
- v1.1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-02*
*Last updated: 2026-03-02 after initial definition*
