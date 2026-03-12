# Phase 9: Auth Polish & Email - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can sign in with Google, recover a forgotten password by email, and receive transactional emails (welcome on signup, receipt on payment, confirmation on cancellation). This phase does not cover onboarding flows, in-app notifications, or email marketing.

</domain>

<decisions>
## Implementation Decisions

### Google Sign-In placement
- Google button appears on BOTH the login page AND the signup page
- Button placed ABOVE the email/password form with an "or" divider below it
- After successful Google sign-in (new or returning), user lands on /chat — same destination as email/password login

### Account collision (existing email+password user tries Google)
- Auto-link accounts silently — Supabase merges the Google identity into the existing account
- User lands on /chat as normal — no prompt, no confirmation step, no duplicate user created

### Email format & tone
- Simple HTML with brand colors — logo/wordmark, minimal layout, no heavy design system
- Tone: warm but concise — first-name greeting, short sentences, no corporate jargon
- Consistent template across all transactional emails (welcome, reset, receipt, cancellation)

### Welcome email
- Content: warm welcome message + single "Start chatting" CTA button linking to /chat
- No feature dump — brief and inviting, not an onboarding guide
- Triggered for ALL new account creation regardless of auth method (email/password AND Google)

### Payment receipt email
- Content: subscription confirmed + amount charged + next billing date + "Manage billing" link
- Clean, transactional, legally safe format

### Cancellation confirmation email
- Content: subscription cancelled + access-until date + re-subscribe link
- Retention-friendly without being pushy

### Password reset
- Unregistered email: returns identical success message as registered email — "If an account exists with this email, a reset link has been sent" — no email enumeration
- Expired/used reset link: dedicated error page with direct link back to the forgot-password form (not a redirect to login)

### Auth error states
- Google OAuth failure (popup blocked, cancelled, permissions denied): inline error below the Google button — "Google sign-in was cancelled. Try again or use email/password."
- Email/password login attempt on a Google-only account (no password set): specific error — "This account was created with Google. Please sign in with Google." — with Google button shown inline

### Google-only accounts (no password)
- "Forgot password" link is hidden or disabled for users who signed up via Google
- Show "Sign in with Google" as their auth path instead

### Email send failure handling
- One automatic retry after a short delay on any send failure
- If retry also fails: log the failure server-side, do NOT block the user action (auth/payment still succeeds)

### Claude's Discretion
- Exact retry delay duration
- Error logging format and destination
- Specific button/divider styling (match existing UI patterns)
- Password reset email copy
- Exact error message wording (within the intent above)

</decisions>

<specifics>
## Specific Ideas

- No specific design references provided — standard Google Sign-In button guidelines apply (Google's official branding)
- Emails should feel like a product you like using, not a bank or SaaS enterprise tool

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-auth-polish-email*
*Context gathered: 2026-03-05*
