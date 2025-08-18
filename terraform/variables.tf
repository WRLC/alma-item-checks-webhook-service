variable "project_name" {
  type        = string
  description = "The name of the project."
  default     = "aic-webhook-service"
}

variable "resource_group_name" {
  type = string
}

variable "app_service_plan_name" {
  type = string
}
variable "webhook_secret" {
  type      = string
  sensitive = true
}
