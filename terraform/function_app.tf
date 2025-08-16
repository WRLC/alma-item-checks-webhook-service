data "azurerm_service_plan" "app_service_plan" {
  name                = var.app_service_plan_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_linux_function_app" "function_app" {
  name                       = "${var.project_name}-${var.service_name}"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  service_plan_id            = data.azurerm_service_plan.app_service_plan.id
  storage_account_name       = azurerm_storage_account.storage_account.name
  storage_account_access_key = azurerm_storage_account.storage_account.primary_access_key

  site_config {
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"     = "1"
    "WEBHOOK_SECRET"               = var.webhook_secret
    "BARCODE_RETRIEVAL_QUEUE_NAME" = local.barcode_retrieval_queue_name
  }

  sticky_settings {
    app_setting_names = [
      "WEBHOOK_SECRET",
      "BARCODE_RETRIEVAL_QUEUE_NAME"
    ]
  }
}

resource "azurerm_linux_function_app_slot" "staging_slot" {
  name                       = "stage"
  function_app_id            = azurerm_linux_function_app.function_app.id
  storage_account_name       = azurerm_storage_account.storage_account.name
  storage_account_access_key = azurerm_storage_account.storage_account.primary_access_key

  site_config {
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"     = "1"
    "WEBHOOK_SECRET"               = var.webhook_secret
    "BARCODE_RETRIEVAL_QUEUE_NAME" = "${local.barcode_retrieval_queue_name}-stage"
  }
}
