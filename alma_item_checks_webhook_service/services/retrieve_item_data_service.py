"""Service to handle barcode events"""
import json
import logging
import time
from typing import Any

import azure.core.exceptions
from requests import RequestException
from wrlc_alma_api_client import AlmaApiClient  # type: ignore
from wrlc_alma_api_client.exceptions import AlmaApiError  # type: ignore
from wrlc_alma_api_client.models import Item  # type: ignore

from alma_item_checks_webhook_service.config import API_CLIENT_TIMEOUT, ITEM_VALIDATION_CONTAINER, ITEM_VALIDATION_QUEUE
from alma_item_checks_webhook_service.models.institution import Institution
from alma_item_checks_webhook_service.database import SessionMaker
from alma_item_checks_webhook_service.services.institution_service import InstitutionService
from alma_item_checks_webhook_service.services.storage_service import StorageService


class RetrieveItemDataService:
    """Service to handle barcode events"""
    def __init__(self, barcode_data: dict[str, Any]):
        """Initialize the BarcodeService class

        Args:
            barcode_data (dict[str, Any]): The barcode data
        """
        self.barcode_data: dict[str, Any] = barcode_data

    def barcode_retrieve(self) -> None:
        """Retrieve item from Alma API by barcode, store data in blob, and queue next action"""
        institution_code: str | None = self.barcode_data.get("institution")
        barcode: str | None = self.barcode_data.get("barcode")
        process: str | None = self.barcode_data.get("process")

        if not institution_code or not barcode:
            logging.error("bp_webhook_barcode_retrieve.webhook_barcode_retrieve: Missing institution or barcode")
            return

        try:
            with SessionMaker() as db:  # get Institution by code
                institution_service: InstitutionService = InstitutionService(db)
                institution: Institution | None = institution_service.get_institution_by_code(code=institution_code)
        except Exception as e:  # catch errors
            logging.error(f"bp_webhook_barcode_retrieve.webhook_barcode_retrieve: Error getting institution: {e}")
            return

        if not institution:  # if no institution, log error and return
            logging.error("bp_webhook_barcode_retrieve.webhook_barcode_retrieve: No institution found")
            raise ValueError("No institution found")

        item_data: Item | None = self.get_item_by_barcode()  # re-retrieve item by barcode

        if not item_data:  # if no item data, log error and return
            logging.warning(
                f"bp_webhook_barcode_retrieve.webhook_barcode_retrieve: No item data returned for barcode {barcode}"
            )
            return

        blob_name: str = f"barcode_{barcode}_iz_{institution.code}.json"  # set blob name
        storage_service: StorageService = StorageService()  # get StorageService

        try:
            storage_service.get_blob_service_client()
            storage_service.upload_blob_data(
                container_name=ITEM_VALIDATION_CONTAINER,
                blob_name=blob_name,
                data=json.dumps(item_data)
            )
        except (ValueError, TypeError, azure.core.exceptions.ServiceRequestError) as e:  # catch errors
            logging.error(f"bp_barcode_retrieval.barcode_retrieve: Error uploading item data to blob: {e}")
            return
        except Exception as e:
            logging.error(f"bp_barcode_retrieval.barcode_retrieve: Unexpected error uploading item data to blob: {e}")
            return

        try:
            storage_service.get_queue_service_client()
            storage_service.send_queue_message(
                queue_name=ITEM_VALIDATION_QUEUE,
                message_content={
                    "institution": institution.code,
                    "blob_name": blob_name,
                    "process": process
                }
            )
        except (ValueError, TypeError, azure.core.exceptions.ServiceRequestError) as e:
            logging.error(
                f"bp_barcode_retrieval.barcode_retrieve: Error sending message to queue for blob {blob_name}: {e}"
            )

    def get_item_by_barcode(self) -> Item | None:
        """Get item by barcode

        Returns:
            Item | None: The item data if found, None otherwise
        """
        institution_code: str | None = self.barcode_data.get("institution")
        barcode: str | None = self.barcode_data.get("barcode")

        if not institution_code or not barcode:
            logging.error("RequestService.get_item_by_barcode: Missing institution or barcode")
            return None

        with SessionMaker() as db:
            institution_service: InstitutionService = InstitutionService(db)
            institution: Institution | None = institution_service.get_institution_by_code(institution_code)

        if not institution or not institution.api_key:
            logging.error(
                f"RequestService.get_item_by_barcode: Could not find institution '{institution_code}' "
                "or it has no API key."
            )
            return None

        alma_client: AlmaApiClient = AlmaApiClient(str(institution.api_key), 'NA', timeout=API_CLIENT_TIMEOUT)

        item_data: Item | None = None
        max_retries: int = 3

        for attempt in range(max_retries):
            try:
                item_data = alma_client.items.get_item_by_barcode(barcode)
                break  # Success, exit the loop
            except RequestException as e:  # Catches timeouts, connection errors, etc.
                logging.warning(
                    f"Attempt {attempt + 1}/{max_retries} to get item {barcode} failed with a network error: {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))  # Wait 2, then 4 seconds before retrying
                else:
                    logging.error(
                        f"All {max_retries} retry attempts failed for barcode {barcode}. Skipping processing."
                    )
                    return None
            except AlmaApiError as e:  # Non-retriable API error (e.g., 404 Not Found)
                logging.warning(f"Error retrieving item {barcode} from Alma, skipping processing: {e}")
                return None

        # Check if the item was found
        if not item_data:
            logging.info(f"Item {barcode} not active in Alma, skipping further processing")
            return None

        return item_data
