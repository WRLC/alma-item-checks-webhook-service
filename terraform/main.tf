data "azurerm_resource_group" "project_rg_shared" {
  name = var.shared_project_resource_group_name
}

data "azurerm_storage_account" "existing" {
  name                = var.shared_storage_account_name
  resource_group_name = data.azurerm_resource_group.project_rg_shared.name
}

data "azurerm_service_plan" "existing" {
  name                = var.app_service_plan_name
  resource_group_name = var.asp_resource_group_name
}

data "azurerm_storage_queue" "fetch_queue" {
  name                = var.fetch_queue_name
  storage_account_name = data.azurerm_storage_account.existing.name
}

data "azurerm_log_analytics_workspace" "existing" {
  name                = var.log_analytics_workspace_name
  resource_group_name = var.law_resource_group_name
}

resource "azurerm_application_insights" "main" {
  name                = var.service_name
  resource_group_name = data.azurerm_resource_group.project_rg_shared.name
  location            = data.azurerm_resource_group.project_rg_shared.location
  application_type    = "web"
  workspace_id        = data.azurerm_log_analytics_workspace.existing.id
}


resource "azurerm_linux_function_app" "function_app" {
  name                       = var.service_name
  resource_group_name        = data.azurerm_resource_group.project_rg_shared.name
  location                   = data.azurerm_resource_group.project_rg_shared.location
  service_plan_id            = data.azurerm_service_plan.existing.id
  storage_account_name       = data.azurerm_storage_account.existing.name
  storage_account_access_key = data.azurerm_storage_account.existing.primary_access_key

  site_config {
    always_on        = true
    application_insights_connection_string = azurerm_application_insights.main.connection_string
    application_insights_key = azurerm_application_insights.main.instrumentation_key
    application_stack {
      python_version = "3.12"
    }
  }


  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"     = "1"
    "WEBHOOK_SECRET"               = var.webhook_secret
    "FETCH_QUEUE_NAME"             = data.azurerm_storage_queue.fetch_queue.name
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
  storage_account_name       = data.azurerm_storage_account.existing.name
  storage_account_access_key = data.azurerm_storage_account.existing.primary_access_key

  site_config {
    always_on        = true
    application_insights_connection_string = azurerm_application_insights.main.connection_string
    application_insights_key = azurerm_application_insights.main.instrumentation_key
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"     = "1"
    "WEBHOOK_SECRET"               = var.webhook_secret
    "FETCH_QUEUE_NAME"             = "${data.azurerm_storage_queue.fetch_queue.name}-stage"
  }
}
