---
created: 2026-03-06T19:19:50.310Z
title: Switch back to live Stripe keys when ready
area: general
files: []
---

## Problem

During email/billing testing, Stripe was switched to test mode and test keys were set in
/opt/ava2/backend/.env (STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET).
Live keys must be restored before accepting real payments.

## Solution

On the VPS:
1. Replace STRIPE_SECRET_KEY with live secret key (sk_live_...)
2. Replace STRIPE_PRICE_ID with live price ID (price_1T7Y6yGzFiJv4RfGhYAwGZM7)
3. Create a live webhook in Stripe Dashboard → Developers → Webhooks pointing to
   https://avasecret.org/billing/webhook with events: checkout.session.completed,
   customer.subscription.deleted, invoice.payment_failed
4. Replace STRIPE_WEBHOOK_SECRET with the live webhook signing secret (whsec_...)
5. docker compose restart backend
6. Verify Stripe Dashboard shows live mode active
