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
