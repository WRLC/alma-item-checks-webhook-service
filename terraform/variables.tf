variable "project_name" {
  type        = string
  description = "The name of the overall project."
  default     = "almaitemchecks"
}

variable "service_name" {
  type        = string
  description = "The name of the specific microservice."
}

variable "resource_group_name" {
  type = string
}

variable "app_service_plan_name" {
  type = string
}

variable "location" {
  type = string
}

variable "mysql_server_name" {
  type = string
}

variable "mysql_admin_username" {
  type      = string
  sensitive = true
}

variable "mysql_admin_password" {
  type      = string
  sensitive = true
}

variable "function_app_name" {
  type = string
}

variable "webhook_secret" {
  type      = string
  sensitive = true
}
