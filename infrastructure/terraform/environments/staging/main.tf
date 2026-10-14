# resource "azurerm_resource_group" "rg" {
#   name     = var.resource_group_name
#   location = var.resource_location
# }


module "storage_bucket" {
  source              = "../../modules/storage_bucket"
  resource_name       = var.storage_resource_name
  resource_group_name = var.staging_resource_group_name
  resource_location   = var.resource_location
}


module "virtual_machine" {
  source                  = "../../modules/virtual_machine"
  resource_group_name     = var.staging_resource_group_name
  resource_location       = var.resource_location
  virtual_network_name    = "staging-attijary-student-vnet"
  subnet_name             = "staging-attijary-student-subnet"
  public_ip_name          = "staging-attijary-student-public-ip"
  domain_name_label       = "staging-attijary-student-public-ip"
  network_interface_name  = "staging-attijary-student-nic"
  virtual_machine_name    = "staging-attijary-student-vm"
  network_security_group_name = "staging-attijary-student-nsg"
  admin_ssh_key= var.STAGING_SSH_PUBLIC_KEY
  management_identity_name = var.management_identity_name
  bootstrap_resource_group_name = var.bootstrap_resource_group_name
}