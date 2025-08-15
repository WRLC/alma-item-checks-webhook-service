"""Configurations for Alma Item Checks Webhook Service"""
import os


def _get_required_env(var_name: str) -> str:
    """Gets a required environment variable or raises a ValueError."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing required environment variable: '{var_name}'")
    return value


STORAGE_CONNECTION_SETTING_NAME = "AzureWebJobsStorage"

STORAGE_CONNECTION_STRING: str = _get_required_env(STORAGE_CONNECTION_SETTING_NAME)
SQLALCHEMY_CONNECTION_STRING: str = _get_required_env("SQLALCHEMY_CONNECTION_STRING")

WEBHOOK_SECRET: str = _get_required_env("WEBHOOK_SECRET")

API_CLIENT_TIMEOUT: int = int(os.getenv("API_CLIENT_TIMEOUT", 90))

BARCODE_RETRIEVAL_QUEUE: str = os.getenv("BARCODE_RETRIEVAL_QUEUE", "barcode-retrieval-queue")
ITEM_VALIDATION_QUEUE: str = os.getenv("ITEM_VALIDATION_QUEUE", "item-validation-queue")

ITEM_VALIDATION_CONTAINER: str = os.getenv("ITEM_VALIDATION_CONTAINER", "item-validation-container")
