"""Service class for handling Webhook events"""
import json
import logging
import os
from typing import Any

import azure.core.exceptions
import azure.functions as func

from alma_item_checks_webhook_service.config import WEBHOOK_SECRET, BARCODE_RETRIEVAL_QUEUE
from alma_item_checks_webhook_service.models.institution import Institution
from alma_item_checks_webhook_service.database import SessionMaker
from alma_item_checks_webhook_service.services.institution_service import InstitutionService
from alma_item_checks_webhook_service.services.storage_service import StorageService
from alma_item_checks_webhook_service.utils.security import validate_webhook_signature


class WebhookService:
    """Service class for handling Webhook events"""
    def __init__(self, req: func.HttpRequest) -> None:
        """Initialize the WebhookService class

        Args:
            req (func.HttpRequest): The request object
        """
        self.req: func.HttpRequest = req

    def parse_webhook(self) -> func.HttpResponse:
        """Parse the webhook and return request data for re-retrieval to verify active status

        Returns:
            func.HttpResponse | dict[str, Any]: A response object if unsuccessful, otherwise request data dictionary
        """
        request_data: func.HttpResponse | dict[str, Any] = self.get_request_data_from_webhook()  # get request data

        if not request_data:  # if request data is missing, return error
            return func.HttpResponse("Internal Server Error: Invalid request data", status_code=500)

        if isinstance(request_data, func.HttpResponse):  # if request data is a response object, return it
            return request_data

        if isinstance(request_data, dict):  # if request data is a dictionary, process it
            barcode: str = (request_data.get("request", {}).get("item_data", {}).get("barcode"))  # get barcode
            if not barcode:  # if no barcode, log and return error
                logging.error("bp_webhook.item_webhook: Barcode not found in webhook payload.")
                return func.HttpResponse("Invalid payload: Barcode is missing.", status_code=400)

            message: dict[str, Any] = {  # create message dictionary
                "institution": request_data.get("institution"),  # item IZ
                "barcode": barcode,  # item barcode
                "process": "item_webhook",  # job (for downstream processing)
            }

            try:
                storage_service: StorageService = StorageService()  # initialize StorageService
                storage_service.get_queue_service_client()  # get queue service client
                storage_service.send_queue_message(  # send message to queue
                    queue_name=BARCODE_RETRIEVAL_QUEUE,  # queue name
                    message_content=message,  # message content
                )
            except (ValueError, TypeError, azure.core.exceptions.ServiceRequestError):  # Catch malformed message
                return func.HttpResponse("Error sending message to queue", status_code=400)

        return func.HttpResponse("Webhook received", status_code=200)

    def get_request_data_from_webhook(self) -> func.HttpResponse | dict[str, Any]:
        """Parse the webhook and return request data for re-retrieval to verify active status

        Returns:
            func.HttpResponse | dict[str, Any]: A response object if unsuccessful, otherwise request data dictionary
        """
        institution: Institution | None = self.get_institution()  # get institution

        if not institution or not isinstance(institution, Institution):  # if institution not found, return error
            return func.HttpResponse("Internal Server Error: Unable to find institution", status_code=500)

        activation: func.HttpResponse | None = self.activate_webhook()  # activate webhook
        if activation:
            if isinstance(activation, func.HttpResponse):  # if activation unsuccessful, return error
                return activation
            return func.HttpResponse("Internal Server Error: Unable to activate webhook", status_code=500)

        if not self.validate_signature():  # if signature invalid, log and raise error
            logging.error("WebhookService.parse_webhook: Invalid webhook signature received.")
            return func.HttpResponse("Internal Server Error: Invalid webhook signature", status_code=500)

        request_data: dict[str, Any] = {  # create request data dictionary
            "institution": institution.code,
            "request": self.req.get_json(),
            "job": "bp_webhook_barcode_re_retrieve"
        }

        return request_data

    def get_institution(self) -> Institution | None:
        """Get the institution

        Returns:
            Institution | None: The institution object if found, None otherwise
        """
        institution_code: str = self.req.params.get("institution")  # get inst code from query param

        if not institution_code:  # if no institution code, log error and return None
            logging.error("WebhookService.parse_webhook: Missing institution parameter")
            return None

        with SessionMaker() as db:  # use DB session
            institution_service: InstitutionService = InstitutionService(db)  # initialize InstitutionService
            institution: Institution | None = institution_service.get_institution_by_code(institution_code)  # get inst

        if not institution:  # if institution not found, log error and return None
            logging.error(f"webhook_service.get_institution: Institution not found: {institution_code}")
            return None

        return institution

    def activate_webhook(self) -> func.HttpResponse | None:
        """Activate the webhook"""
        if self.req.method != 'POST':
            if self.req.params.get("challenge"):

                challenge_response: dict[str, str] = {"challenge": self.req.params.get("challenge")}

                return func.HttpResponse(
                    json.dumps(challenge_response),
                    mimetype="application/json",
                    status_code=200
                )
        return None

    def validate_signature(self) -> bool:
        """Validate the signature"""
        is_local_dev: bool = os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT") == "Development"

        if not is_local_dev:
            if not validate_webhook_signature(
                self.req.get_body(), WEBHOOK_SECRET, self.req.headers.get("X-Exl-Signature")
            ):
                logging.error("RequestService.validate_signature: Invalid webhook signature received.")
                return False

        return True
