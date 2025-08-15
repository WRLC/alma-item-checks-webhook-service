resource "random_string" "storage_account_suffix" {
  length  = 10
  special = false
  upper   = false
}

resource "azurerm_storage_account" "storage_account" {
  name                     = "${var.project_name}${random_string.storage_account_suffix.result}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

locals {
  barcode_retrieval_queue_name = "barcode-retrieval-queue"
  item_validation_queue_name   = "item-validation-queue"
  item_validation_container_name = "item-validation-container"
}

resource "azurerm_storage_queue" "barcode_retrieval_queue" {
  name                 = local.barcode_retrieval_queue_name
  storage_account_name = azurerm_storage_account.storage_account.name
}

resource "azurerm_storage_queue" "item_validation_queue" {
  name                 = local.item_validation_queue_name
  storage_account_name = azurerm_storage_account.storage_account.name
}

resource "azurerm_storage_container" "item_validation_container" {
  name                  = local.item_validation_container_name
  storage_account_id    = azurerm_storage_account.storage_account.id
  container_access_type = "private"
}

# Stage Storage Resources
resource "azurerm_storage_queue" "stage_barcode_retrieval_queue" {
  name                 = "${local.barcode_retrieval_queue_name}-stage"
  storage_account_name = azurerm_storage_account.storage_account.name
}

resource "azurerm_storage_queue" "stage_item_validation_queue" {
  name                 = "${local.item_validation_queue_name}-stage"
  storage_account_name = azurerm_storage_account.storage_account.name
}

resource "azurerm_storage_container" "stage_item_validation_container" {
  name                  = "${local.item_validation_container_name}-stage"
  storage_account_id    = azurerm_storage_account.storage_account.id
  container_access_type = "private"
}
