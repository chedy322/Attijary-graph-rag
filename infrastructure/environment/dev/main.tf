resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.resource_location
}


module "storage_bucket" {
  source              = "../../modules/storage_bucket"
  resource_name       = var.resource_name
  resource_group_name = azurerm_resource_group.rg.name
  resource_location   = azurerm_resource_group.rg.location
}


# module "virtual_machine" {
#   source                  = "../../modules/virtual_machine"
#   resource_group_name     = azurerm_resource_group.rg.name
#   resource_location       = azurerm_resource_group.rg.location
#   virtual_network_name    = "attijary-student-vnet"
#   subnet_name             = "attijary-student-subnet"
#   public_ip_name          = "attijary-student-public-ip"
#   domain_name_label       = "attijary-student-public-ip"
#   network_interface_name  = "attijary-student-nic"
#   virtual_machine_name    = "attijary-student-vm"
#   network_security_group_name = "attijary-student-nsg"
#   admin_ssh_key= var.admin_ssh_key
# }