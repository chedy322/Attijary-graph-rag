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


variable "STAGING_SSH_PUBLIC_KEY" {
  description = "The SSH public key for the virtual machine."
  type        = string
}

variable "staging_resource_group_name" {
  description = "The name of the staging resource group."
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



variable "management_identity_name" {
  description = "The name of the user-assigned managed identity."
  type        = string
}

