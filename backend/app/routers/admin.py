"""
Admin router — operator-only endpoints.

GET /admin/metrics  — returns 5 metrics across 3 time windows (7d, 30d, all-time).

Access control:
  require_admin dependency checks user.is_super_admin from the Supabase user object.
  Set via Supabase Dashboard: Authentication > Users > [user] > toggle "is_super_admin".
  Uses is_super_admin (Supabase-managed, service-role only) — NOT user_metadata (user-settable).

Data sources (mixed — not all from usage_events):
  - active_users: auth.users.last_sign_in_at (via supabase_admin.auth.admin.list_users())
  - new_signups: auth.users.created_at (same list_users() call)
  - active_subscriptions: subscriptions table, status='active'
  - messages_sent: usage_events table, event_type='message_sent'
  - photos_generated: usage_events table, event_type='photo_generated'
"""
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import supabase_admin
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(user=Depends(get_current_user)):
    """
    Extends get_current_user — raises 403 if user is not a Supabase super admin.
    Admin status set via Supabase Dashboard: Authentication > Users > toggle "is_super_admin".
    SECURITY: reads app_metadata.role (service-role managed), NOT user_metadata (user-settable).
    Set via Supabase Dashboard SQL: raw_app_meta_data = '{"role": "super_admin"}'.
    Add directly in admin.py — not a global dependency (anti-pattern per RESEARCH.md).
    """
    is_admin = (user.app_metadata or {}).get("role") == "super_admin"
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


def _cutoff_iso(days: int | None) -> str | None:
    """Return ISO 8601 datetime string for `days` ago, or None for all-time."""
    if days is None:
        return None
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _count_events(event_type: str, days: int | None) -> int:
    """Count usage_events rows of given type within time window. All-time if days=None."""
    query = (
        supabase_admin.from_("usage_events")
        .select("id", count="exact")
        .eq("event_type", event_type)
    )
    cutoff = _cutoff_iso(days)
    if cutoff is not None:
        query = query.gte("created_at", cutoff)
    result = query.execute()
    return result.count or 0


def _count_active_subscriptions() -> int:
    """Count subscriptions with status='active'. All-time (subscriptions are current state)."""
    result = (
        supabase_admin.from_("subscriptions")
        .select("id", count="exact")
        .eq("status", "active")
        .execute()
    )
    return result.count or 0


def _get_user_metrics() -> dict:
    """
    Fetch all users via auth.admin.list_users() and compute active_users + new_signups.
    # TODO: paginate for >1000 users (list_users() returns max 1000 by default)
    Returns dict with 7d/30d/all counts for both metrics.
    """
    try:
        users_response = supabase_admin.auth.admin.list_users()
        # supabase-py v2: list_users() returns a list of UserModel objects
        all_users = users_response if isinstance(users_response, list) else list(users_response)
    except Exception as e:
        logger.error("Failed to list users from Supabase auth.admin: %s", e)
        return {
            "active_users": {"d7": 0, "d30": 0, "all": 0},
            "new_signups": {"d7": 0, "d30": 0, "all": 0},
        }

    now = datetime.now(timezone.utc)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)

    def _parse_dt(val) -> datetime | None:
        """Parse datetime from string or datetime object; return None on failure."""
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.replace(tzinfo=timezone.utc) if val.tzinfo is None else val
        try:
            # Supabase returns ISO strings — strip trailing Z, parse
            return datetime.fromisoformat(str(val).rstrip("Z")).replace(tzinfo=timezone.utc)
        except Exception:
            return None

    active_7d = active_30d = active_all = 0
    new_7d = new_30d = new_all = 0

    for u in all_users:
        last_sign = _parse_dt(getattr(u, "last_sign_in_at", None))
        created = _parse_dt(getattr(u, "created_at", None))

        if last_sign:
            active_all += 1
            if last_sign >= cutoff_30d:
                active_30d += 1
            if last_sign >= cutoff_7d:
                active_7d += 1
        elif created:
            # New user who has never signed in — count as active at creation time
            active_all += 1

        if created:
            new_all += 1
            if created >= cutoff_30d:
                new_30d += 1
            if created >= cutoff_7d:
                new_7d += 1

    return {
        "active_users": {"d7": active_7d, "d30": active_30d, "all": active_all},
        "new_signups": {"d7": new_7d, "d30": new_30d, "all": new_all},
    }


@router.get("/metrics")
async def get_metrics(user=Depends(require_admin)):
    """
    Return 5 product health metrics, each with 7d / 30d / all-time counts.
    Manual refresh only — no polling. Admin-only (require_admin raises 403 for non-admins).

    Response shape:
    {
      "active_users":         {"d7": int, "d30": int, "all": int},
      "messages_sent":        {"d7": int, "d30": int, "all": int},
      "photos_generated":     {"d7": int, "d30": int, "all": int},
      "active_subscriptions": {"d7": int, "d30": int, "all": int},
      "new_signups":          {"d7": int, "d30": int, "all": int},
      "fetched_at": "ISO datetime string"
    }

    Note: active_subscriptions d7/d30 counts active subscriptions created in that window.
    The "all" count is total currently-active subscriptions (current state, not historical).
    """
    try:
        user_metrics = _get_user_metrics()

        # messages_sent and photos_generated from usage_events table
        messages_sent = {
            "d7":  _count_events("message_sent", 7),
            "d30": _count_events("message_sent", 30),
            "all": _count_events("message_sent", None),
        }
        photos_generated = {
            "d7":  _count_events("photo_generated", 7),
            "d30": _count_events("photo_generated", 30),
            "all": _count_events("photo_generated", None),
        }

        # active_subscriptions: current state (all = total active now)
        # d7/d30: subscriptions created in that window that are still active
        active_subs_all = _count_active_subscriptions()

        def _count_active_subs_since(days: int) -> int:
            cutoff = _cutoff_iso(days)
            result = (
                supabase_admin.from_("subscriptions")
                .select("id", count="exact")
                .eq("status", "active")
                .gte("created_at", cutoff)
                .execute()
            )
            return result.count or 0

        active_subscriptions = {
            "d7":  _count_active_subs_since(7),
            "d30": _count_active_subs_since(30),
            "all": active_subs_all,
        }

        return {
            "active_users":         user_metrics["active_users"],
            "messages_sent":        messages_sent,
            "photos_generated":     photos_generated,
            "active_subscriptions": active_subscriptions,
            "new_signups":          user_metrics["new_signups"],
            "fetched_at":           datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to compute admin metrics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch admin metrics")
