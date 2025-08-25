variable "tf_shared_resource_group_name" {
  type = string
}

variable "tf_shared_storage_account_name" {
  type = string
}

variable "tf_shared_container_name" {
  type = string
}

variable "tf_shared_key" {
  type = string
}

variable "webhook_secret" {
  type      = string
  sensitive = true
}
