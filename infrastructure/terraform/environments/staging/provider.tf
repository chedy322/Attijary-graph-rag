terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.10"
    }

  }
  backend "azurerm" {
    resource_group_name   = "my-bootstrap-rg"
    storage_account_name  = "attijarymystatestorage7"
    container_name        = "mytfstatecontainerstaging"
    key                   = "staging.tfstate"
    use_azuread_auth       = true
  }
}


provider "azurerm" {
  features {}
  storage_use_azuread = true
}
