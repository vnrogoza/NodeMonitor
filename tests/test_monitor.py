import requests
from unittest.mock import Mock, patch

import monitor


def test_build_webhook_payload_success_event():
    payload = monitor.build_webhook_payload("https://example.com", 200, 123.45, None)

    assert payload["event"] == "monitor_success"
    assert payload["url"] == "https://example.com"
    assert payload["status_code"] == 200
    assert payload["error_message"] is None


def test_build_webhook_payload_failure_event():
    payload = monitor.build_webhook_payload("https://example.com", 500, 300.0, "timeout")

    assert payload["event"] == "monitor_failure"
    assert payload["url"] == "https://example.com"
    assert payload["status_code"] == 500
    assert payload["error_message"] == "timeout"


def test_format_report_data():
    rows = [("2026-04-12 12:00", 100.0, "blue")]
    result = monitor.format_report_data(rows)

    assert "2026-04-12 12:00" in result
    assert "100.0" in result
    assert "blue" in result


@patch("monitor.requests.post")
def test_send_webhook_notification_success(mock_post):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = monitor.send_webhook_notification("https://webhook.test", {"event": "monitor_failure"})

    mock_post.assert_called_once_with(
        "https://webhook.test",
        json={"event": "monitor_failure"},
        timeout=monitor.WEBHOOK_TIMEOUT_SECONDS,
    )
    assert result is True


@patch("monitor.requests.post")
def test_send_webhook_notification_failure(mock_post):
    mock_post.side_effect = requests.RequestException("failed")

    result = monitor.send_webhook_notification("https://webhook.test", {"event": "monitor_failure"})

    assert result is False
