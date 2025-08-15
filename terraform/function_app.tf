resource "azurerm_service_plan" "app_service_plan" {
  name                = "${var.project_name}-app-service-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption Plan
}

resource "azurerm_linux_function_app" "function_app" {
  name                       = var.function_app_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  service_plan_id            = azurerm_service_plan.app_service_plan.id
  storage_account_name       = azurerm_storage_account.storage_account.name
  storage_account_access_key = azurerm_storage_account.storage_account.primary_access_key

  site_config {
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    "SQLALCHEMY_CONNECTION_STRING" = "mysql+pymysql://${mysql_user.user.user}:${random_password.mysql_user_password.result}@${var.mysql_server_name}.mysql.database.azure.com/${azurerm_mysql_flexible_database.database.name}"
    "WEBHOOK_SECRET"               = var.webhook_secret
    "BARCODE_RETRIEVAL_QUEUE_NAME" = local.barcode_retrieval_queue_name
    "ITEM_VALIDATION_QUEUE_NAME"   = local.item_validation_queue_name
    "ITEM_VALIDATION_CONTAINER_NAME" = local.item_validation_container_name
  }

  sticky_settings {
    app_setting_names = [
      "SQLALCHEMY_CONNECTION_STRING",
      "WEBHOOK_SECRET",
      "BARCODE_RETRIEVAL_QUEUE_NAME",
      "ITEM_VALIDATION_QUEUE_NAME",
      "ITEM_VALIDATION_CONTAINER_NAME"
    ]
  }
}

resource "azurerm_linux_function_app_slot" "staging_slot" {
  name            = "stage"
  function_app_id = azurerm_linux_function_app.function_app.id

  site_config {
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    "SQLALCHEMY_CONNECTION_STRING" = "mysql+pymysql://${mysql_user.stage_user.user}:${random_password.stage_mysql_user_password.result}@${var.mysql_server_name}.mysql.database.azure.com/${azurerm_mysql_flexible_database.stage_database.name}"
    "WEBHOOK_SECRET"               = var.webhook_secret
    "BARCODE_RETRIEVAL_QUEUE_NAME" = "${local.barcode_retrieval_queue_name}-stage"
    "ITEM_VALIDATION_QUEUE_NAME"   = "${local.item_validation_queue_name}-stage"
    "ITEM_VALIDATION_CONTAINER_NAME" = "${local.item_validation_container_name}-stage"
  }
}
