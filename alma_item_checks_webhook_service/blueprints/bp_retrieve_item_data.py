"""Retrieve item from Alma API by barcode, store data in blob, and queue next action"""
import json
from typing import Any

import azure.functions as func

from alma_item_checks_webhook_service.config import BARCODE_RETRIEVAL_QUEUE, STORAGE_CONNECTION_SETTING_NAME
from alma_item_checks_webhook_service.services.retrieve_item_data_service import RetrieveItemDataService

bp: func.Blueprint = func.Blueprint()


@bp.function_name("retrieve_item_data")
@bp.queue_trigger(
    arg_name="barcodemsg",
    queue_name=BARCODE_RETRIEVAL_QUEUE,
    connection=STORAGE_CONNECTION_SETTING_NAME
)
def retrieve_item_data(barcodemsg: func.QueueMessage) -> None:
    """Retrieve item from Alma API by barcode, store data in blob, and queue next action

    Args:
        barcodemsg (func.QueueMessage): Queue message
    """
    barcode_data: dict[str, Any] = json.loads(barcodemsg.get_body().decode())  # get barcode data

    retrieve_item_data_service: RetrieveItemDataService = RetrieveItemDataService(barcode_data)  # initialize service
    retrieve_item_data_service.barcode_retrieve()  # retrieve barcode
