"""Test suite for item_webhook function"""
from unittest.mock import Mock

import azure.functions as func

from alma_item_checks_webhook_service.blueprints.bp_webhook import item_webhook


def test_item_webhook(mocker):
    """Test item_webhook function"""
    # given
    mock_request = func.HttpRequest(
        method='POST',
        url='/api/scfwebhook',
        body=b'{"test": "body"}'
    )
    mock_response = func.HttpResponse("mock response", status_code=200)

    mock_webhook_service = Mock()
    mock_webhook_service.parse_webhook.return_value = mock_response

    mock_webhook_service_class = mocker.patch(
        'alma_item_checks_webhook_service.blueprints.bp_webhook.WebhookService',
        return_value=mock_webhook_service
    )

    # when
    response = item_webhook(mock_request)

    # then
    mock_webhook_service_class.assert_called_once_with(mock_request)
    mock_webhook_service.parse_webhook.assert_called_once()
    assert response == mock_response
