# Phase 11: Subscription Management & Churn - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

A dedicated `/billing` page where authenticated subscribed users can view their subscription info, manage payment details via Stripe Customer Portal, upgrade their plan, and cancel with a two-question survey flow. Covers the full cancellation UX including post-cancellation state and expired subscription handling.

</domain>

<decisions>
## Implementation Decisions

### Billing page layout
- Dedicated `/billing` route — its own page, not a section within settings
- Required fields visible at top: plan name, current status, next billing date
- Invoice history section below: simple list with date, amount, status — each links to Stripe-hosted PDF in new tab
- Three actions present: **Manage billing** button (prominent), **Upgrade** button (prominent), **Cancel** link (small, less visually prominent — e.g., small text link below the action buttons)

### Cancellation flow
- Flow: Cancel link → Survey Q1 → Survey Q2 → Final confirm button (survey-confirm-last pattern)
- Survey Q1: "What did you like most about Ava?" — free text, skippable
- Survey Q2: "Why are you leaving?" — free text, skippable
- Final step: "Yes, cancel my subscription" button to confirm cancellation
- After confirmation: stay on `/billing`, page shows updated state (Resubscribe option visible)
- Tone of confirmation message: warm, low-regret — e.g., "We're sad to see you go. You'll keep access until [date]."

### Post-cancellation state (cancel_at_period_end)
- No prominent banner or alert showing cancellation status — intentionally low-key
- Only visible change: the Cancel link becomes a **Resubscribe** link/button
- Status field continues to show "Active" — no "Cancelling" badge
- Resubscribe click → opens Stripe Customer Portal (new tab)
- When subscription fully expires: redirect expired users to upgrade/paywall on app entry — not a custom expired billing page

### Upgrade flow
- Upgrade button opens an **in-app upgrade modal** showing plan options/pricing before any Stripe redirect
- Modal handles the upgrade path; after user confirms, routes to Stripe checkout

### Stripe Portal navigation
- "Manage billing" opens Stripe Customer Portal in a **new tab**
- Stripe `return_url` configured to `/billing`
- Billing page auto-refreshes subscription data when the user tabs back (window focus event triggers re-fetch)

### Claude's Discretion
- Exact visual design, spacing, and typography of the billing page
- Loading/skeleton states while fetching subscription data
- Error states (Stripe API unavailable, portal session creation failure)
- Exact survey skip mechanism (Skip button vs empty submit vs "Skip and cancel" link)

</decisions>

<specifics>
## Specific Ideas

- Cancel should be present but visually de-emphasized (small link, not a button) — friction-appropriate without being dark-pattern manipulative
- Cancellation survey questions are positively framed first ("What did you like most?") before asking why they're leaving — warm exit
- Post-cancellation: the app should feel normal, not punitive. Users keep access and the UI doesn't keep reminding them they cancelled.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-subscription-management-churn*
*Context gathered: 2026-03-09*
