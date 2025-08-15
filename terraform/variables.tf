variable "resource_group_name" {
  type        = string
  description = "The name of the resource group for the Function App and its resources."
}

variable "mysql_resource_group_name" {
  type        = string
  description = "The name of the resource group for the MySQL server."
}

variable "location" {
  type        = string
  description = "The Azure region in which to create the resources."
}

variable "mysql_server_name" {
  type        = string
  description = "The name of the MySQL Flexible Server in which to create the database."
}

variable "project_name" {
  type        = string
  description = "The name of the project."
  default     = "almaitemchecks"
}

variable "mysql_admin_username" {
  type        = string
  description = "The administrator username for the MySQL server."
  sensitive   = true
}

variable "mysql_admin_password" {
  type        = string
  description = "The administrator password for the MySQL server."
  sensitive   = true
}

variable "mysql_user_username" {
  type        = string
  description = "The username for the application's MySQL user."
  default     = "almaitemchecks_user"
}

variable "function_app_name" {
  type        = string
  description = "The name of the Function App."
}

variable "webhook_secret" {
  type        = string
  description = "The secret for the webhook."
  sensitive   = true
}

variable "app_service_plan_name" {
  type        = string
  description = "The name of the existing App Service Plan."
}
