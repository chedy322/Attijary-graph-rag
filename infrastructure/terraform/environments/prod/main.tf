# resource "azurerm_resource_group" "rg" {
#   name     = var.resource_group_name
#   location = var.resource_location
# }


module "storage_bucket" {
  source              = "../../modules/storage_bucket"
  resource_name       = var.storage_resource_name
  resource_group_name = var.prod_resource_group_name
  resource_location   = var.resource_location
}


module "virtual_machine" {
  source                  = "../../modules/virtual_machine"
  resource_group_name     = var.prod_resource_group_name
  resource_location       = var.resource_location
  virtual_network_name    = "attijary-student-vnet"
  subnet_name             = "attijary-student-subnet"
  public_ip_name          = "attijary-student-public-ip"
  domain_name_label       = "attijary-student-public-ip"
  network_interface_name  = "attijary-student-nic"
  virtual_machine_name    = "attijary-student-vm"
  network_security_group_name = "attijary-student-nsg"
  admin_ssh_key= var.admin_ssh_key
  management_identity_name = var.management_identity_name
  bootstrap_resource_group_name = var.bootstrap_resource_group_name
}