"""Test suite for StorageService"""
from unittest.mock import Mock

import pytest
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.data.tables import UpdateMode

from alma_item_checks_webhook_service.services.storage_service import StorageService


@pytest.fixture
def mock_azure_clients(mocker):
    """Fixture to mock all Azure service clients and their specific clients."""
    # Mock the main service clients
    mock_blob_service_client = mocker.patch(
        'alma_item_checks_webhook_service.services.storage_service.BlobServiceClient'
    ).from_connection_string.return_value
    mock_queue_service_client = mocker.patch(
        'alma_item_checks_webhook_service.services.storage_service.QueueServiceClient'
    ).from_connection_string.return_value
    mock_table_service_client = mocker.patch(
        'alma_item_checks_webhook_service.services.storage_service.TableServiceClient'
    ).from_connection_string.return_value

    # Mock the specific clients returned by the service clients
    mocks = {
        'blob_service_client': mock_blob_service_client,
        'queue_service_client': mock_queue_service_client,
        'table_service_client': mock_table_service_client,
        'blob_client': mock_blob_service_client.get_blob_client.return_value,
        'container_client': mock_blob_service_client.get_container_client.return_value,
        'queue_client': mock_queue_service_client.get_queue_client.return_value,
        'table_client': mock_table_service_client.get_table_client.return_value,
    }
    # Also mock the standalone QueueClient.from_connection_string
    mocker.patch(
        'alma_item_checks_webhook_service.services.storage_service.QueueClient.from_connection_string',
        return_value=mocks['queue_client']
    )
    return mocks


@pytest.fixture
def storage_service():
    """Fixture to provide an instance of the StorageService."""
    return StorageService()


class TestBlobStorage:
    """Tests for Azure Blob Storage functionality."""

    def test_upload_blob_data_dict(self, storage_service, mock_azure_clients):
        data = {"key": "value"}
        storage_service.upload_blob_data("test-container", "test.json", data)
        mock_azure_clients['blob_client'].upload_blob.assert_called_once()
        # More specific assertions can be added for content_settings etc.

    def test_upload_blob_overwrite_false_exists(self, storage_service, mock_azure_clients):
        mock_azure_clients['blob_client'].upload_blob.side_effect = ResourceExistsError("Blob exists")
        with pytest.raises(ResourceExistsError):
            storage_service.upload_blob_data("test-container", "test.blob", "data", overwrite=False)

    def test_download_blob_as_text_success(self, storage_service, mock_azure_clients):
        mock_blob_download = mock_azure_clients['blob_client'].download_blob.return_value
        mock_blob_download.readall.return_value = b'some text data'
        content = storage_service.download_blob_as_text("test-container", "test.txt")
        assert content == "some text data"

    def test_download_blob_not_found(self, storage_service, mock_azure_clients):
        mock_azure_clients['blob_client'].download_blob.side_effect = ResourceNotFoundError("Not found")
        with pytest.raises(ResourceNotFoundError):
            storage_service.download_blob_as_text("test-container", "nonexistent.txt")

    def test_list_blobs_success(self, storage_service, mock_azure_clients):
        mock_blob1, mock_blob2 = Mock(), Mock()
        mock_blob1.name = "blob1.txt"
        mock_blob2.name = "blob2.txt"
        mock_azure_clients['container_client'].list_blobs.return_value = [mock_blob1, mock_blob2]
        blobs = storage_service.list_blobs("test-container")
        assert blobs == ["blob1.txt", "blob2.txt"]


class TestQueueStorage:
    """Tests for Azure Queue Storage functionality."""

    def test_send_queue_message_dict(self, storage_service, mock_azure_clients):
        message = {"id": 123, "action": "process"}
        storage_service.send_queue_message("test-queue", message)
        mock_azure_clients['queue_client'].send_message.assert_called_once_with(
            content='{"id": 123, "action": "process"}'
        )

    def test_send_queue_message_str(self, storage_service, mock_azure_clients):
        message = "a plain string message"
        storage_service.send_queue_message("test-queue", message)
        mock_azure_clients['queue_client'].send_message.assert_called_once_with(content=message)


class TestTableStorage:
    """Tests for Azure Table Storage functionality."""

    def test_upsert_entity_success(self, storage_service, mock_azure_clients, mocker):
        entity = {"PartitionKey": "pk", "RowKey": "rk", "Data": "test"}
        mock_create_table = mocker.patch.object(storage_service, 'create_table_if_not_exists')
        storage_service.upsert_entity("test-table", entity)
        mock_create_table.assert_called_once_with("test-table")
        mock_azure_clients['table_client'].upsert_entity.assert_called_once_with(entity=entity, mode=UpdateMode.REPLACE)

    def test_get_entities_with_filter(self, storage_service, mock_azure_clients):
        mock_entity = {"PartitionKey": "pk", "RowKey": "rk1"}
        mock_azure_clients['table_client'].query_entities.return_value = [mock_entity]
        entities = storage_service.get_entities("test-table", filter_query="RowKey eq 'rk1'")
        assert entities == [mock_entity]
        mock_azure_clients['table_client'].query_entities.assert_called_once_with(query_filter="RowKey eq 'rk1'")

    def test_delete_entity_success(self, storage_service, mock_azure_clients):
        storage_service.delete_entity("test-table", "pk", "rk")
        mock_azure_clients['table_client'].delete_entity.assert_called_once_with(partition_key="pk", row_key="rk")

    def test_create_table_if_not_exists(self, storage_service, mock_azure_clients):
        storage_service.create_table_if_not_exists("new-table")
        mock_azure_clients['table_service_client'].create_table.assert_called_once_with(table_name="new-table")

    def test_create_table_already_exists(self, storage_service, mock_azure_clients):
        mock_azure_clients['table_service_client'].create_table.side_effect = ResourceExistsError()
        # Should not raise an error
        storage_service.create_table_if_not_exists("existing-table")
