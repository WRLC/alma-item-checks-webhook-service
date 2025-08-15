"""Service class for handling Webhook events"""

import json
import logging
import os
from typing import Any

import azure.core.exceptions
import azure.functions as func

from alma_item_checks_webhook_service.config import (
    WEBHOOK_SECRET,
    BARCODE_RETRIEVAL_QUEUE,
)
from alma_item_checks_webhook_service.models.institution import Institution
from alma_item_checks_webhook_service.database import SessionMaker
from alma_item_checks_webhook_service.services.institution_service import (
    InstitutionService,
)
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
        # First, check for a challenge request and handle it immediately.
        activation_response = self.activate_webhook()
        if activation_response:
            return activation_response

        request_data: func.HttpResponse | dict[str, Any] = (
            self.get_request_data_from_webhook()
        )

        if not request_data or isinstance(request_data, func.HttpResponse):
            return request_data or func.HttpResponse(
                "Internal Server Error: Invalid request data", status_code=500
            )

        if isinstance(request_data, dict):
            barcode: str = (
                request_data.get("request", {}).get("item_data", {}).get("barcode")
            )
            if not barcode:
                logging.error(
                    "bp_webhook.item_webhook: Barcode not found in webhook payload."
                )
                return func.HttpResponse(
                    "Invalid payload: Barcode is missing.", status_code=400
                )

            message: dict[str, Any] = {
                "institution": request_data.get("institution"),
                "barcode": barcode,
                "process": "item_webhook",
            }

            try:
                storage_service: StorageService = StorageService()
                storage_service.send_queue_message(
                    queue_name=BARCODE_RETRIEVAL_QUEUE,
                    message_content=message,
                )
            except (
                ValueError,
                TypeError,
                azure.core.exceptions.ServiceRequestError,
            ) as e:
                logging.error(f"Failed to send message to queue: {e}")
                return func.HttpResponse(
                    "Error sending message to queue", status_code=500
                )

        return func.HttpResponse("Webhook received", status_code=200)

    def get_request_data_from_webhook(self) -> func.HttpResponse | dict[str, Any]:
        """Parse the webhook and return request data for re-retrieval to verify active status

        Returns:
            func.HttpResponse | dict[str, Any]: A response object if unsuccessful, otherwise request data dictionary
        """
        institution: Institution | None = self.get_institution()

        if not institution:
            return func.HttpResponse(
                "Internal Server Error: Unable to find institution", status_code=500
            )

        if not self.validate_signature():
            logging.error(
                "WebhookService.parse_webhook: Invalid webhook signature received."
            )
            return func.HttpResponse(
                "Internal Server Error: Invalid webhook signature", status_code=500
            )

        try:
            request_body = self.req.get_json()
        except ValueError:
            logging.error(
                "WebhookService.get_request_data_from_webhook: Invalid JSON in request body."
            )
            return func.HttpResponse("Invalid JSON in request body", status_code=400)

        return {
            "institution": institution.code,
            "request": request_body,
            "job": "bp_webhook_barcode_re_retrieve",
        }

    def get_institution(self) -> Institution | None:
        """Get the institution

        Returns:
            Institution | None: The institution object if found, None otherwise
        """
        institution_code: str = self.req.params.get("institution")

        if not institution_code:
            logging.error(
                "WebhookService.get_institution: Missing institution parameter"
            )
            return None

        with SessionMaker() as db:
            institution_service: InstitutionService = InstitutionService(db)
            institution: Institution | None = (
                institution_service.get_institution_by_code(institution_code)
            )

        if not institution:
            logging.error(
                f"webhook_service.get_institution: Institution not found: {institution_code}"
            )
            return None

        return institution

    def activate_webhook(self) -> func.HttpResponse | None:
        """Activate the webhook by responding to a challenge request."""
        if self.req.method == "GET" and self.req.params.get("challenge"):
            challenge_response = {"challenge": self.req.params.get("challenge")}
            return func.HttpResponse(
                json.dumps(challenge_response),
                mimetype="application/json",
                status_code=200,
            )
        return None

    def validate_signature(self) -> bool:
        """Validate the signature"""
        if os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT") == "Development":
            return True

        if not validate_webhook_signature(
            self.req.get_body(), WEBHOOK_SECRET, self.req.headers.get("X-Exl-Signature")
        ):
            logging.error(
                "RequestService.validate_signature: Invalid webhook signature received."
            )
            return False

        return True
