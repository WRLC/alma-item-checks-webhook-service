variable "service_name" {
  type        = string
}

variable "shared_project_resource_group_name" {
  type = string
}

variable "shared_storage_account_name" {
  type = string
}

variable "fetch_queue_name" {
  type = string
}

variable "asp_resource_group_name" {
  type = string
}

variable "app_service_plan_name" {
  type = string
}

variable "log_analytics_workspace_name" {
  type = string
}

variable "law_resource_group_name" {
  type = string
}

variable "webhook_secret" {
  type      = string
  sensitive = true
}
