# variable "resource_group_name" {
#   description = "The name of the resource group."
#   type        = string
# }

variable "resource_location" {
  description = "The location of the resource."
  type        = string
}

variable "storage_resource_name" {
  description = "The name of the resource."
  type        = string
}


variable "admin_ssh_key" {
  description = "The SSH public key for the virtual machine."
  type        = string
}

variable "prod_resource_group_name" {
  description = "The name of the production resource group."
  type        = string
}

variable "bootstrap_resource_group_name" {
  description = "The name of the bootstrap resource group."
  type        = string
}
variable "terraform_state_storage_account_name" {
  description = "The name of the storage account for Terraform state."
  type        = string
}
variable "terraform_state_prod_container_name" {
  description = "The name of the container for Terraform state in production."
  type        = string
}


variable "management_identity_name" {
  description = "The name of the user-assigned managed identity."
  type        = string
}

