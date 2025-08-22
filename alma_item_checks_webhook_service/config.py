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

WEBHOOK_SECRET: str = _get_required_env("WEBHOOK_SECRET")

FETCH_ITEM_QUEUE: str = os.getenv("FETCH_ITEM_QUEUE", "fetch-item-queue")
