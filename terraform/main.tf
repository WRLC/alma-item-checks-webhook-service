terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.1"
    }
    mysql = {
      source  = "petoju/mysql"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
}

provider "mysql" {
  endpoint = "${var.mysql_server_name}.mysql.database.azure.com:3306"
  username = var.mysql_admin_username
  password = var.mysql_admin_password
}
