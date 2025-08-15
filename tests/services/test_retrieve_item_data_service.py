import json
from unittest.mock import Mock

import pytest
from requests import RequestException
from wrlc_alma_api_client.exceptions import AlmaApiError  # type: ignore

from alma_item_checks_webhook_service.models.institution import Institution
from alma_item_checks_webhook_service.services.retrieve_item_data_service import (
    RetrieveItemDataService,
)


@pytest.fixture
def mock_dependencies(mocker):
    """Mock all external dependencies for the service."""
    mocks = {
        "SessionMaker": mocker.patch(
            "alma_item_checks_webhook_service.services.retrieve_item_data_service.SessionMaker"
        ),
        "InstitutionService": mocker.patch(
            "alma_item_checks_webhook_service.services.retrieve_item_data_service.InstitutionService"
        ),
        "StorageService": mocker.patch(
            "alma_item_checks_webhook_service.services.retrieve_item_data_service.StorageService"
        ),
        "AlmaApiClient": mocker.patch(
            "alma_item_checks_webhook_service.services.retrieve_item_data_service.AlmaApiClient"
        ),
        "time": mocker.patch("time.sleep"),  # Mock time.sleep for retry logic
    }
    # Mock the context manager for SessionMaker
    mock_session = Mock()
    mocks["SessionMaker"].return_value.__enter__.return_value = mock_session

    # Mock service instances
    mocks["mock_institution_service"] = mocks["InstitutionService"].return_value
    mocks["mock_storage_service"] = mocks["StorageService"].return_value
    mocks["mock_alma_client"] = mocks["AlmaApiClient"].return_value

    return mocks


@pytest.fixture
def mock_institution():
    """Return a mock institution object."""
    return Institution(id=1, name="Test University", code="TU", api_key="fake_api_key")


class TestBarcodeRetrieve:
    """Tests for the barcode_retrieve method."""

    def test_barcode_retrieve_success(self, mock_dependencies, mock_institution):
        """Test the happy path for barcode_retrieve."""
        # Arrange
        barcode_data = {
            "institution": "TU",
            "barcode": "12345",
            "process": "test_process",
        }
        item_data = {"bib_data": {"mms_id": "99123"}}

        service = RetrieveItemDataService(barcode_data)
        # Mock the service's own method to isolate the test to barcode_retrieve logic
        service.get_item_by_barcode = Mock(return_value=item_data)

        mock_dependencies[
            "mock_institution_service"
        ].get_institution_by_code.return_value = mock_institution

        # Act
        service.barcode_retrieve()

        # Assert
        mock_dependencies["InstitutionService"].assert_called_once()
        mock_dependencies[
            "mock_institution_service"
        ].get_institution_by_code.assert_called_once_with(code="TU")
        service.get_item_by_barcode.assert_called_once()

        expected_blob_name = "barcode_12345_iz_TU.json"
        mock_dependencies["mock_storage_service"].upload_blob_data.assert_called_once_with(
            container_name="item-validation-container",
            blob_name=expected_blob_name,
            data=json.dumps(item_data),
        )
        mock_dependencies[
            "mock_storage_service"
        ].send_queue_message.assert_called_once_with(
            queue_name="item-validation-queue",
            message_content={
                "institution": "TU",
                "blob_name": expected_blob_name,
                "process": "test_process",
            },
        )

    def test_missing_barcode_or_institution(self, caplog):
        """Test that the function exits early if barcode or institution is missing."""
        service = RetrieveItemDataService({"barcode": "12345"})  # Missing institution
        service.barcode_retrieve()
        assert "Missing institution or barcode" in caplog.text

    def test_institution_not_found(self, mock_dependencies, caplog):
        """Test that a ValueError is raised if the institution is not found."""
        mock_dependencies[
            "mock_institution_service"
        ].get_institution_by_code.return_value = None
        service = RetrieveItemDataService({"institution": "NONE", "barcode": "12345"})

        with pytest.raises(ValueError, match="No institution found"):
            service.barcode_retrieve()
        assert "No institution found" in caplog.text

    def test_item_data_not_found(self, mock_dependencies, mock_institution, caplog):
        """Test that the function exits if no item data is returned."""
        service = RetrieveItemDataService({"institution": "TU", "barcode": "12345"})
        service.get_item_by_barcode = Mock(return_value=None)
        mock_dependencies[
            "mock_institution_service"
        ].get_institution_by_code.return_value = mock_institution

        service.barcode_retrieve()

        assert "No item data returned for barcode 12345" in caplog.text
        mock_dependencies["mock_storage_service"].upload_blob_data.assert_not_called()


class TestGetItemByBarcode:
    """Tests for the get_item_by_barcode method."""

    def test_get_item_by_barcode_success(self, mock_dependencies, mock_institution):
        """Test happy path for get_item_by_barcode."""
        mock_dependencies[
            "mock_institution_service"
        ].get_institution_by_code.return_value = mock_institution
        mock_item = Mock()
        mock_dependencies[
            "mock_alma_client"
        ].items.get_item_by_barcode.return_value = mock_item

        service = RetrieveItemDataService({"institution": "TU", "barcode": "12345"})
        item = service.get_item_by_barcode()

        assert item == mock_item
        mock_dependencies["AlmaApiClient"].assert_called_once_with(
            "fake_api_key", "NA", timeout=90
        )
        mock_dependencies[
            "mock_alma_client"
        ].items.get_item_by_barcode.assert_called_once_with("12345")

    def test_get_item_network_error_with_retry(
        self, mock_dependencies, mock_institution, caplog
    ):
        """Test that a network error is retried."""
        mock_dependencies[
            "mock_institution_service"
        ].get_institution_by_code.return_value = mock_institution
        mock_dependencies["mock_alma_client"].items.get_item_by_barcode.side_effect = (
            RequestException("Connection failed")
        )

        service = RetrieveItemDataService({"institution": "TU", "barcode": "12345"})
        item = service.get_item_by_barcode()

        assert item is None
        assert (
            mock_dependencies["mock_alma_client"].items.get_item_by_barcode.call_count
            == 3
        )
        assert mock_dependencies["time"].call_count == 2
        assert "All 3 retry attempts failed for barcode 12345" in caplog.text

    def test_get_item_alma_api_error_no_retry(
        self, mock_dependencies, mock_institution, caplog
    ):
        """Test that a non-retriable Alma API error is not retried."""
        mock_dependencies[
            "mock_institution_service"
        ].get_institution_by_code.return_value = mock_institution
        mock_dependencies["mock_alma_client"].items.get_item_by_barcode.side_effect = (
            AlmaApiError("Item not found", status_code=404)
        )

        service = RetrieveItemDataService({"institution": "TU", "barcode": "12345"})
        item = service.get_item_by_barcode()

        assert item is None
        assert (
            mock_dependencies["mock_alma_client"].items.get_item_by_barcode.call_count
            == 1
        )
        assert "Error retrieving item 12345 from Alma" in caplog.text
