"""Tests for the WebhookService class"""
import json
from unittest.mock import Mock

import pytest
import azure.functions as func

from alma_item_checks_webhook_service.services.webhook_service import WebhookService


@pytest.fixture
def mock_request_factory():
    """Factory to create mock HttpRequest objects."""

    def _create_mock_request(
        method="POST",
        params=None,
        headers=None,
        body=b'{"event": {"value": "ITEM_UPDATED"}, "item": {"item_data": {"barcode": "12345"}}, "institution": {"value": "TU"}}',
    ):
        default_headers = {"X-Exl-Signature": "valid_signature"}
        req = func.HttpRequest(
            method=method,
            url="/api/scfwebhook",
            params=params or {},
            headers=headers or default_headers,
            body=body,
        )
        # Add get_json method to the mock request
        req.get_json = Mock(return_value=json.loads(body.decode()) if body else {})
        return req

    return _create_mock_request


@pytest.fixture
def mock_dependencies(mocker):
    """Mock all external dependencies for the WebhookService."""
    mock_storage_service = mocker.patch(
        "alma_item_checks_webhook_service.services.webhook_service.StorageService",
        autospec=True,
    )

    mocks = {
        "StorageService": mock_storage_service,
        "validate_webhook_signature": mocker.patch(
            "alma_item_checks_webhook_service.services.webhook_service.validate_webhook_signature"
        ),
        "os_environ": mocker.patch("os.environ.get", return_value="Production"),
    }
    mocks["mock_storage_service"] = mocks["StorageService"].return_value
    return mocks


class TestParseWebhook:
    """Tests for the main parse_webhook method."""

    def test_parse_webhook_success(self, mock_request_factory, mock_dependencies):
        """Test the happy path for a valid webhook POST request."""
        req = mock_request_factory()
        mock_dependencies["validate_webhook_signature"].return_value = True

        service = WebhookService(req)
        response = service.parse_webhook()

        assert response.status_code == 200
        assert response.get_body() == b"Webhook received"
        mock_dependencies["mock_storage_service"].send_queue_message.assert_called_once()

    def test_parse_webhook_challenge_request(self, mock_request_factory):
        """Test that a GET request with a challenge is handled correctly."""
        req = mock_request_factory(method="GET", params={"challenge": "test_challenge"}, body=b'')
        service = WebhookService(req)
        response = service.parse_webhook()

        assert response.status_code == 200
        assert json.loads(response.get_body()) == {"challenge": "test_challenge"}

    def test_parse_webhook_missing_barcode(self, mock_request_factory, mock_dependencies, caplog):
        """Test that a webhook with a missing barcode returns a 400 error."""
        req = mock_request_factory(body=b'{"event": {"value": "ITEM_UPDATED"}, "item": {"item_data": {}}, "institution": {"value": "TU"}}')  # No barcode
        mock_dependencies["validate_webhook_signature"].return_value = True

        service = WebhookService(req)
        response = service.parse_webhook()

        assert response.status_code == 400
        assert b"Invalid payload: Barcode is missing." in response.get_body()
        assert "Barcode not found in webhook payload" in caplog.text

    def test_parse_webhook_non_item_updated_event(self, mock_request_factory, mock_dependencies):
        """Test that a webhook with a non-ITEM_UPDATED event returns 200 but doesn't process."""
        req = mock_request_factory(body=b'{"event": {"value": "ITEM_CREATED"}, "item": {"item_data": {"barcode": "12345"}}, "institution": {"value": "TU"}}')
        mock_dependencies["validate_webhook_signature"].return_value = True

        service = WebhookService(req)
        response = service.parse_webhook()

        assert response.status_code == 200
        assert response.get_body() == b"Webhook received"
        # Should not call send_queue_message for non-ITEM_UPDATED events
        mock_dependencies["mock_storage_service"].send_queue_message.assert_not_called()

    def test_parse_webhook_invalid_signature(self, mock_request_factory, mock_dependencies, caplog):
        """Test that an invalid signature returns a 500 error."""
        req = mock_request_factory()
        mock_dependencies["validate_webhook_signature"].return_value = False

        service = WebhookService(req)
        response = service.parse_webhook()

        assert response.status_code == 500
        assert b"Invalid webhook signature" in response.get_body()
        assert "Invalid webhook signature received" in caplog.text


class TestValidateSignature:
    """Tests for the validate_signature helper method."""

    def test_validate_signature_prod_valid(self, mock_request_factory, mock_dependencies):
        req = mock_request_factory()
        mock_dependencies["validate_webhook_signature"].return_value = True
        service = WebhookService(req)
        assert service.validate_signature() is True

    def test_validate_signature_prod_invalid(self, mock_request_factory, mock_dependencies, caplog):
        req = mock_request_factory()
        mock_dependencies["validate_webhook_signature"].return_value = False
        service = WebhookService(req)
        assert service.validate_signature() is False
        assert "Invalid webhook signature received" in caplog.text

    def test_validate_signature_dev_env(self, mock_request_factory, mock_dependencies):
        """Test that signature validation is skipped in a development environment."""
        req = mock_request_factory()
        mock_dependencies["os_environ"].return_value = "Development"
        service = WebhookService(req)
        assert service.validate_signature() is True
        # Ensure the actual validation function was not called
        mock_dependencies["validate_webhook_signature"].assert_not_called()

    def test_parse_webhook_storage_service_error(self, mock_request_factory, mock_dependencies, caplog):
        """Test that a storage service error returns a 500 error."""
        req = mock_request_factory()
        mock_dependencies["validate_webhook_signature"].return_value = True
        # Make the storage service throw an exception
        mock_dependencies["mock_storage_service"].send_queue_message.side_effect = ValueError("Storage error")

        service = WebhookService(req)
        response = service.parse_webhook()

        assert response.status_code == 500
        assert b"Error sending message to queue" in response.get_body()
        assert "Failed to send message to queue: Storage error" in caplog.text

    def test_get_request_data_missing_institution(self, mock_request_factory, mock_dependencies, caplog):
        """Test that missing institution.value in request body returns a 400 error."""
        req = mock_request_factory(body=b'{"event": {"value": "ITEM_UPDATED"}, "item": {"item_data": {"barcode": "12345"}}}')  # No institution
        mock_dependencies["validate_webhook_signature"].return_value = True

        service = WebhookService(req)
        response = service.get_request_data_from_webhook()

        assert response.status_code == 400
        assert b"Missing institution.value in request body" in response.get_body()
        assert "Missing institution.value in request body" in caplog.text

    def test_get_request_data_invalid_json(self, mock_request_factory, mock_dependencies, caplog):
        """Test that invalid JSON in request body returns a 400 error."""
        req = mock_request_factory()
        mock_dependencies["validate_webhook_signature"].return_value = True
        # Make get_json throw a ValueError
        req.get_json = Mock(side_effect=ValueError("Invalid JSON"))

        service = WebhookService(req)
        response = service.get_request_data_from_webhook()

        assert response.status_code == 400
        assert b"Invalid JSON in request body" in response.get_body()
        assert "Invalid JSON in request body" in caplog.text
