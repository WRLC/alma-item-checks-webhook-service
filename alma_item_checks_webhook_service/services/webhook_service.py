"""Service class for handling Webhook events"""

import json
import logging
import os
from typing import Any

import azure.core.exceptions
import azure.functions as func

from alma_item_checks_webhook_service.config import WEBHOOK_SECRET, FETCH_QUEUE_NAME
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

        if not isinstance(request_data, dict):
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
                from wrlc_azure_storage_service import StorageService  # type: ignore

                storage_service = StorageService()
                storage_service.send_queue_message(
                    queue_name=FETCH_QUEUE_NAME,
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
        if not self.validate_signature():
            logging.error(
                "WebhookService.parse_webhook: Invalid webhook signature received."
            )
            return func.HttpResponse(
                "Internal Server Error: Invalid webhook signature", status_code=500
            )
        try:
            institution_code: str | None = self.req.params.get("institution")
            if not institution_code:
                logging.error(
                    "WebhookService.get_request_data_from_webhook: Missing institution parameter"
                )
                return func.HttpResponse(
                    "Missing institution parameter", status_code=400
                )
        except ValueError:
            logging.error(
                "WebhookService.get_request_data_from_webhook: Invalid institution parameter"
            )
            return func.HttpResponse("Invalid institution parameter", status_code=400)

        try:
            request_body = self.req.get_json()
        except ValueError:
            logging.error(
                "WebhookService.get_request_data_from_webhook: Invalid JSON in request body."
            )
            return func.HttpResponse("Invalid JSON in request body", status_code=400)

        return {
            "institution": institution_code,
            "request": request_body,
            "job": "bp_webhook_barcode_re_retrieve",
        }

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
