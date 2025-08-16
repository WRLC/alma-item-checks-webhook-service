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

variable "function_app_name" {
  type = string
}

variable "webhook_secret" {
  type      = string
  sensitive = true
}
