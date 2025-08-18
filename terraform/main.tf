data "azurerm_resource_group" "existing" {
  name = var.resource_group_name
}

data "azurerm_service_plan" "existing" {
  name                = var.app_service_plan_name
  resource_group_name = data.azurerm_resource_group.existing.name
}

resource "azurerm_storage_account" "storage_account" {
  name                     = replace(var.project_name, "-", "")
  resource_group_name      = data.azurerm_resource_group.existing.name
  location                 = data.azurerm_resource_group.existing.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

locals {
  fetch_queue_name = "fetch-queue"
  queues_to_create = toset([
    local.fetch_queue_name,
    "${local.fetch_queue_name}-stage"
  ])
}

resource "azurerm_storage_queue" "fetch_queues" {
  for_each             = local.queues_to_create
  name                 = each.key
  storage_account_name = azurerm_storage_account.storage_account.name
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-la"
  location            = data.azurerm_resource_group.existing.location
  resource_group_name = data.azurerm_resource_group.existing.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "main" {
  name                = var.project_name
  resource_group_name = data.azurerm_resource_group.existing.name
  location            = data.azurerm_resource_group.existing.location
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id
}


resource "azurerm_linux_function_app" "function_app" {
  name                       = var.project_name
  resource_group_name        = data.azurerm_resource_group.existing.name
  location                   = data.azurerm_resource_group.existing.location
  service_plan_id            = data.azurerm_service_plan.existing.id
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
    "FETCH_QUEUE_NAME" = local.fetch_queue_name
  }

  sticky_settings {
    app_setting_names = [
      "FETCH_QUEUE_NAME"
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
    "FETCH_QUEUE_NAME" = "${local.fetch_queue_name}-stage"
  }
}
