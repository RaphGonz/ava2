---
created: 2026-03-06T19:19:50.310Z
title: Finish Google OAuth validation
area: auth
files:
  - frontend/src/pages/LandingPage.tsx
  - frontend/src/pages/PrivacyPage.tsx
  - frontend/src/pages/TermsPage.tsx
---

## Problem

Google OAuth consent screen requires full app verification before going public. Four requirements raised by Google:
1. Homepage must link to privacy policy — done (LandingPage.tsx has /privacy link)
2. Homepage must explain app purpose — done (LandingPage.tsx has description)
3. App name "Avasecret" must match homepage — done
4. Domain ownership verification via Google Search Console — NOT YET DONE

Also pending:
- Add privacy policy URL (https://avasecret.org/privacy) to OAuth consent screen in Google Cloud Console
- Add terms URL (https://avasecret.org/terms) to OAuth consent screen
- Fill in governing law section in TermsPage.tsx (section 10 — currently [PLACEHOLDER]) after attorney review
- Update takedown email if takedown@avasecret.org is not yet active

## Solution

1. Google Search Console → Add property https://avasecret.org → DNS verification → add TXT record in Hetzner DNS → verify
2. Google Cloud Console → APIs & Services → OAuth consent screen → set Privacy Policy URL + Terms URL → resubmit for verification
3. After attorney review: replace [PLACEHOLDER] in TermsPage.tsx section 10 with actual governing law jurisdiction
