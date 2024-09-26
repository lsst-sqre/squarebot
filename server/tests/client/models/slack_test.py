"""Test parsing Slack payloads."""

from __future__ import annotations

from pathlib import Path

import pytest

from rubin.squarebot.models.slack import (
    SlackBlockActionsPayload,
    SlackViewSubmissionPayload,
)


@pytest.fixture
def samples_dir() -> Path:
    """Get the path to the samples directory for interactions."""
    return Path(__file__).parent / "../../slack_messages/interactions"


def test_parse_block_actions_static_select(samples_dir: Path) -> None:
    """Test parsing a block action with a static select."""
    data = SlackBlockActionsPayload.model_validate_json(
        (samples_dir / "block_actions/static_select.json").read_text()
    )
    assert data.type == "block_actions"
    assert data.container.type == "message"
    assert data.actions[0].type == "static_select"
    assert data.actions[0].action_id == "templatebot_select_project_template"
    assert data.actions[0].selected_option.value == "fastapi"
    assert data.actions[0].selected_option.text.text == "FastAPI"


def test_parse_view_submission(samples_dir: Path) -> None:
    """Test parsing a view_submission."""
    data = SlackViewSubmissionPayload.model_validate_json(
        (samples_dir / "view_submission.json").read_text()
    )
    assert data.type == "view_submission"
