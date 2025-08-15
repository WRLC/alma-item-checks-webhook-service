import pytest
from alma_item_checks_webhook_service.utils.security import validate_webhook_signature


@pytest.fixture
def sample_data():
    """Provides sample data for testing."""
    return {
        "body": b'{"key": "value"}',
        "secret": "test_secret",
        # This signature is pre-calculated for the body and secret
        "valid_signature": "n9h4nbtY6kgo0ns104I3W2khZH0lM9oiVLqLlmyeb+U=",
    }


def test_validate_webhook_signature_valid(sample_data):
    """Test that a valid signature returns True."""
    assert validate_webhook_signature(
        body_bytes=sample_data["body"],
        secret=sample_data["secret"],
        received_signature=sample_data["valid_signature"],
    )


def test_validate_webhook_signature_invalid(sample_data):
    """Test that an invalid signature returns False."""
    assert not validate_webhook_signature(
        body_bytes=sample_data["body"],
        secret=sample_data["secret"],
        received_signature="invalid_signature",
    )


def test_validate_webhook_signature_missing_signature(sample_data, caplog):
    """Test that a missing signature returns False and logs a warning."""
    assert not validate_webhook_signature(
        body_bytes=sample_data["body"],
        secret=sample_data["secret"],
        received_signature=None,
    )
    assert "X-Exl-Signature header is missing" in caplog.text


def test_validate_webhook_signature_missing_secret(sample_data, caplog):
    """Test that a missing secret returns False and logs an error."""
    assert not validate_webhook_signature(
        body_bytes=sample_data["body"],
        secret=None,
        received_signature=sample_data["valid_signature"],
    )
    assert "Webhook secret is not provided for validation" in caplog.text
