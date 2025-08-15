"""Test suite for retrieve_item_data function"""
import json
from unittest.mock import Mock

import azure.functions as func

from alma_item_checks_webhook_service.blueprints.bp_retrieve_item_data import (
    retrieve_item_data,
)


def test_retrieve_item_data(mocker):
    """Test retrieve_item_data function"""
    # given
    barcode = "12345"
    queue_message_body = json.dumps({"barcode": barcode}).encode()
    queue_message = func.QueueMessage(body=queue_message_body)

    mock_retrieve_item_data_service = Mock()
    mocker.patch(
        "alma_item_checks_webhook_service.blueprints.bp_retrieve_item_data.RetrieveItemDataService",
        return_value=mock_retrieve_item_data_service,
    )

    # when
    retrieve_item_data(queue_message)

    # then
    mock_retrieve_item_data_service.barcode_retrieve.assert_called_once()
