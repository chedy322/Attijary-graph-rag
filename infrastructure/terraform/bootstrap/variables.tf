# Prod environment variables
variable "prod_resource_group_name" {
  description = "The name of the resource group to create."
  type        = string
}


# Staging environment variables
variable "staging_resource_group_name" {
  description = "The name of the resource group to create."
  type        = string
}
variable "staging_storage_account_name" {
  description = "The name of the storage account to create."
  type        = string
}

variable "staging_storage_account_location" {
  description = "The location of the storage account to create."
  type        = string
}

# General variables for resource group and storage account names
variable "bootstrap_resource_group_name" {
  description = "The name of the resource group to create."
  type        = string
}

variable "terraform_state_storage_account_name" {
  description = "The name of the storage account to create."
  type        = string
}

variable "terraform_state_storage_account_location" {
  description = "The location of the storage account to create."
  type        = string
}

variable "terraform_state_statging_container_name" {
  description = "The name of the storage container to create."
  type        = string
}
variable "terraform_state_prod_container_name" {
  description = "The name of the storage container to create."
  type        = string
}
variable "resource_location" {
  description = "The location of the resource group to create."
  type        = string
}

# variable "bootstrap_resource_group_name" {
#   description = "The name of the resource group to create."
#   type        = string
# }