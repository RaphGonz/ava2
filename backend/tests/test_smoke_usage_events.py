"""
Smoke test: usage_events table has all 4 required event types (ADMN-02).
Queries production Supabase directly via service role key.
Prerequisites:
  - Production backend/.env must be accessible, OR
  - SUPABASE_URL and SUPABASE_SERVICE_KEY env vars set to production values
Run: cd backend && python -m pytest tests/test_smoke_usage_events.py -x -v
"""
import pytest

REQUIRED_EVENT_TYPES = [
    "message_sent",
    "photo_generated",
    "mode_switch",
    "subscription_created",
]


def test_all_required_event_types_present():
    """
    Confirms all 4 required event types have accumulated at least 1 row
    in the production usage_events table.
    """
    try:
        from app.database import supabase_admin
    except Exception as e:
        pytest.skip(f"Cannot import supabase_admin (production DB not configured): {e}")

    missing = []
    for event_type in REQUIRED_EVENT_TYPES:
        try:
            result = (
                supabase_admin.from_("usage_events")
                .select("id", count="exact")
                .eq("event_type", event_type)
                .execute()
            )
            count = result.count or 0
            if count == 0:
                missing.append(event_type)
        except Exception as e:
            pytest.skip(f"DB query failed (production DB may not be reachable): {e}")

    assert not missing, (
        f"Missing usage_events rows for event_type(s): {missing}\n"
        "Ensure production has processed at least one event of each type."
    )
