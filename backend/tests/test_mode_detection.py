"""Tests for ModeSwitchDetector — slash commands, fuzzy phrases, and edge cases."""
import pytest
from app.services.mode_detection.detector import detect_mode_switch, DetectionResult
from app.services.session.models import ConversationMode


class TestSlashCommands:
    """Exact slash command detection must always be confidence='exact'."""

    def test_intimate_slash(self):
        result = detect_mode_switch("/intimate", ConversationMode.SECRETARY)
        assert result.target == ConversationMode.INTIMATE
        assert result.confidence == "exact"

    def test_secretary_slash(self):
        result = detect_mode_switch("/secretary", ConversationMode.INTIMATE)
        assert result.target == ConversationMode.SECRETARY
        assert result.confidence == "exact"

    def test_stop_slash(self):
        result = detect_mode_switch("/stop", ConversationMode.INTIMATE)
        assert result.target == ConversationMode.SECRETARY
        assert result.confidence == "exact"

    def test_slash_with_leading_space(self):
        result = detect_mode_switch("  /intimate  ", ConversationMode.SECRETARY)
        assert result.confidence == "exact"


class TestFuzzyIntimateDetection:
    """Fuzzy match for intimate mode triggers."""

    def test_im_alone_exact_phrase(self):
        result = detect_mode_switch("i'm alone", ConversationMode.SECRETARY)
        assert result.target == ConversationMode.INTIMATE
        assert result.confidence == "fuzzy"

    def test_im_alone_typo(self):
        result = detect_mode_switch("im alone", ConversationMode.SECRETARY)
        assert result.target == ConversationMode.INTIMATE
        assert result.confidence in ("exact", "fuzzy")  # high confidence either way

    def test_lets_be_alone(self):
        result = detect_mode_switch("lets be alone", ConversationMode.SECRETARY)
        assert result.target == ConversationMode.INTIMATE
        assert result.confidence == "fuzzy"


class TestFuzzySecretaryDetection:
    """Fuzzy match for secretary mode triggers."""

    def test_stop(self):
        result = detect_mode_switch("stop", ConversationMode.INTIMATE)
        assert result.target == ConversationMode.SECRETARY
        assert result.confidence == "fuzzy"

    def test_back_to_work(self):
        result = detect_mode_switch("back to work", ConversationMode.INTIMATE)
        assert result.target == ConversationMode.SECRETARY
        assert result.confidence == "fuzzy"


class TestNormalMessages:
    """Normal chat messages must not be misclassified as mode switches."""

    def test_greeting(self):
        result = detect_mode_switch("Hello, how are you?", ConversationMode.SECRETARY)
        assert result.confidence == "none"
        assert result.target is None

    def test_weather_question(self):
        result = detect_mode_switch("What's the weather today?", ConversationMode.SECRETARY)
        assert result.confidence == "none"

    def test_long_sentence_with_stop_word(self):
        # "stop" alone is a trigger, but in a long sentence it should not fire
        result = detect_mode_switch(
            "I'm done and want to stop the project analysis right now",
            ConversationMode.INTIMATE,
        )
        assert result.confidence == "none", (
            "Long sentences with trigger words should not fire mode switch"
        )
