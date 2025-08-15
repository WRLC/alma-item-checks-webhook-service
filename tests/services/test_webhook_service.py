import json
from unittest.mock import Mock, patch

import pytest
import azure.functions as func

from alma_item_checks_webhook_service.models.institution import Institution
from alma_item_checks_webhook_service.services.webhook_service import WebhookService


@pytest.fixture
def mock_request_factory():
    """Factory to create mock HttpRequest objects."""

    def _create_mock_request(
        method="POST",
        params=None,
        headers=None,
        body=b'{"item_data": {"barcode": "12345"}}',
    ):
        req = func.HttpRequest(
            method=method,
            url="/api/scfwebhook",
            params=params if params is not None else {"institution": "TU"},
            headers=headers or {"X-Exl-Signature": "valid_signature"},
            body=body,
        )
        # Add get_json method to the mock request
        req.get_json = Mock(return_value=json.loads(body.decode('utf-8')) if body else {})
        return req

    return _create_mock_request


@pytest.fixture
def mock_dependencies(mocker):
    """Mock all external dependencies for the WebhookService."""
    mocks = {
        "SessionMaker": mocker.patch(
            "alma_item_checks_webhook_service.services.webhook_service.SessionMaker"
        ),
        "InstitutionService": mocker.patch(
            "alma_item_checks_webhook_service.services.webhook_service.InstitutionService"
        ),
        "StorageService": mocker.patch(
            "alma_item_checks_webhook_service.services.webhook_service.StorageService"
        ),
        "validate_webhook_signature": mocker.patch(
            "alma_item_checks_webhook_service.services.webhook_service.validate_webhook_signature"
        ),
        "os_environ": mocker.patch("os.environ.get", return_value="Production"),
    }
    mock_session = Mock()
    mocks["SessionMaker"].return_value.__enter__.return_value = mock_session
    mocks["mock_institution_service"] = mocks["InstitutionService"].return_value
    mocks["mock_storage_service"] = mocks["StorageService"].return_value
    return mocks


@pytest.fixture
def mock_institution():
    """Return a mock institution object."""
    return Institution(id=1, name="Test University", code="TU", api_key="fake_api_key")


class TestParseWebhook:
    """Tests for the main parse_webhook method."""

    def test_parse_webhook_success(self, mock_request_factory, mock_dependencies, mock_institution):
        """Test the happy path for a valid webhook POST request."""
        req = mock_request_factory()
        mock_dependencies["mock_institution_service"].get_institution_by_code.return_value = mock_institution
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

    def test_parse_webhook_missing_barcode(self, mock_request_factory, mock_dependencies, mock_institution, caplog):
        """Test that a webhook with a missing barcode returns a 400 error."""
        req = mock_request_factory(body=b'{"item_data": {}}') # No barcode
        mock_dependencies["mock_institution_service"].get_institution_by_code.return_value = mock_institution
        mock_dependencies["validate_webhook_signature"].return_value = True

        service = WebhookService(req)
        response = service.parse_webhook()

        assert response.status_code == 400
        assert b"Invalid payload: Barcode is missing." in response.get_body()
        assert "Barcode not found in webhook payload" in caplog.text

    def test_parse_webhook_invalid_signature(self, mock_request_factory, mock_dependencies, mock_institution, caplog):
        """Test that an invalid signature returns a 500 error."""
        req = mock_request_factory()
        mock_dependencies["mock_institution_service"].get_institution_by_code.return_value = mock_institution
        mock_dependencies["validate_webhook_signature"].return_value = False

        service = WebhookService(req)
        response = service.parse_webhook()

        assert response.status_code == 500
        assert b"Invalid webhook signature" in response.get_body()
        assert "Invalid webhook signature received" in caplog.text


class TestGetInstitution:
    """Tests for the get_institution helper method."""

    def test_get_institution_success(self, mock_request_factory, mock_dependencies, mock_institution):
        req = mock_request_factory()
        mock_dependencies["mock_institution_service"].get_institution_by_code.return_value = mock_institution
        service = WebhookService(req)
        institution = service.get_institution()
        assert institution is not None
        assert institution.code == "TU"

    def test_get_institution_missing_param(self, mock_request_factory, mock_dependencies, caplog):
        req = mock_request_factory(params={})
        service = WebhookService(req)
        institution = service.get_institution()
        assert institution is None
        assert "Missing institution parameter" in caplog.text

    def test_get_institution_not_found(self, mock_request_factory, mock_dependencies, caplog):
        req = mock_request_factory()
        mock_dependencies["mock_institution_service"].get_institution_by_code.return_value = None
        service = WebhookService(req)
        institution = service.get_institution()
        assert institution is None
        assert "Institution not found: TU" in caplog.text


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
