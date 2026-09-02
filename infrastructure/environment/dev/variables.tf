variable "resource_group_name" {
  description = "The name of the resource group."
  type        = string
}

variable "resource_location" {
  description = "The location of the resource."
  type        = string
}

variable "resource_name" {
  description = "The name of the resource."
  type        = string
}


variable "admin_ssh_key" {
  description = "The SSH public key for the virtual machine."
  type        = string
}