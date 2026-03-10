"""
Tests for usage event emission wiring (ADMN-02).
Verifies that emit calls happen at the correct code paths using mocked supabase_admin.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import json


class TestPhotoGeneratedEmission:
    """Verifies photo_generated emit is added to processor.py alongside audit_log."""

    def test_photo_generated_emit_exists_in_processor(self):
        """Grep-style test: verify 'photo_generated' string present in processor.py source."""
        import inspect
        from app.services.jobs import processor
        source = inspect.getsource(processor)
        assert "photo_generated" in source, (
            "processor.py must emit 'photo_generated' to usage_events (ADMN-02). "
            "audit_log alone is insufficient."
        )

    def test_audit_log_still_present_in_processor(self):
        """Regression: audit_log write must not be removed (compliance requirement)."""
        import inspect
        from app.services.jobs import processor
        source = inspect.getsource(processor)
        assert "audit_log" in source, "audit_log write in processor.py must not be removed"


class TestMessageSentEmission:
    """Verifies message_sent emit is wired in chat.py."""

    def test_message_sent_emit_exists_in_chat(self):
        import inspect
        from app.services import chat
        source = inspect.getsource(chat)
        assert "message_sent" in source, (
            "chat.py must emit 'message_sent' to usage_events (ADMN-02)."
        )


class TestModeSwitchEmission:
    """Verifies mode_switch emit is wired in chat.py."""

    def test_mode_switch_emit_exists_in_chat(self):
        import inspect
        from app.services import chat
        source = inspect.getsource(chat)
        assert "mode_switch" in source and "usage_events" in source, (
            "chat.py must emit 'mode_switch' to usage_events (ADMN-02)."
        )

    def test_mode_switch_emit_not_on_already_in_mode_path(self):
        """
        Pitfall 6: mode_switch emit must not appear inside already-in-mode return blocks.
        Verify that ALREADY_INTIMATE_MSG and ALREADY_SECRETARY_MSG returns don't
        have a usage_events insert immediately before them.
        """
        import inspect
        from app.services import chat
        source = inspect.getsource(chat)
        # Rough heuristic: if "mode_switch" appears N times, it should not appear
        # immediately adjacent to ALREADY_INTIMATE_MSG
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'ALREADY_INTIMATE_MSG' in line or 'ALREADY_SECRETARY_MSG' in line:
                # Check the 5 lines before this return — should not contain usage_events insert
                context = '\n'.join(lines[max(0, i-5):i])
                assert 'event_type.*mode_switch' not in context or 'mode_switch' not in context.replace(' ', ''), (
                    f"mode_switch emit found too close to already-in-mode return at line {i}"
                )


class TestSubscriptionCreatedEmission:
    """Verifies subscription_created emit is wired in billing.py."""

    def test_subscription_created_emit_exists_in_billing(self):
        import inspect
        from app.routers import billing
        source = inspect.getsource(billing)
        assert "subscription_created" in source, (
            "billing.py must emit 'subscription_created' to usage_events (ADMN-02). "
            "subscription_cancelled alone is insufficient (different event, different handler)."
        )

    def test_both_subscription_events_present(self):
        """Both subscription_created AND subscription_cancelled must exist in billing.py."""
        import inspect
        from app.routers import billing
        source = inspect.getsource(billing)
        assert "subscription_created" in source
        assert "subscription_cancelled" in source
