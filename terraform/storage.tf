resource "random_string" "storage_account_suffix" {
  length  = 10
  special = false
  upper   = false
}

resource "azurerm_storage_account" "storage_account" {
  name                     = "${replace(var.service_name, "-", "")}${random_string.storage_account_suffix.result}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

locals {
  barcode_retrieval_queue_name = "${var.service_name}-barcode-retrieval-queue"
}

resource "azurerm_storage_queue" "barcode_retrieval_queue" {
  name                 = local.barcode_retrieval_queue_name
  storage_account_name = azurerm_storage_account.storage_account.name
}

# Stage Storage Resources
resource "azurerm_storage_queue" "stage_barcode_retrieval_queue" {
  name                 = "${local.barcode_retrieval_queue_name}-stage"
  storage_account_name = azurerm_storage_account.storage_account.name
}
