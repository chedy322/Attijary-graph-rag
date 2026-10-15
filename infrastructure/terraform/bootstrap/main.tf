data "azurerm_client_config" "current" {}

# Create the resource group
resource "azurerm_resource_group" "bootstrap_rg" {
  name     = var.bootstrap_resource_group_name
  location = var.resource_location
}


resource "azurerm_resource_group" "prod_rg" {
  name     = var.prod_resource_group_name
  location = var.resource_location
}

# Create the tfstate bucket
# Create the tfstate Storage resource and its related resources with two containers inside it, one for prod and one for staging. The containers are private and can only be accessed by the CI/CD pipeline using the storage account key. The public can only read the blobs in the container but cannot write to it.
# No public access
resource "azurerm_storage_account" "tfstate_storage" {
  name                            = var.terraform_state_storage_account_name
  resource_group_name             = azurerm_resource_group.bootstrap_rg.name
  location                        = var.terraform_state_storage_account_location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  public_network_access_enabled   = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = true
  #   
  depends_on = [azurerm_resource_group.bootstrap_rg]
}

resource "time_sleep" "wait_for_storage" {
  depends_on      = [azurerm_storage_account.tfstate_storage]
  create_duration = "30s"
}

resource "azurerm_storage_container" "prod_container" {
  name               = var.terraform_state_prod_container_name
  storage_account_id = azurerm_storage_account.tfstate_storage.id
  # Changed access_type to "private" to make the container private
  container_access_type = "private"
}

# Create key vault for prod 
resource "azurerm_key_vault" "prod_kv" {
  name                       = "${var.prod_resource_group_name}-kv"
  location                   = var.resource_location
  resource_group_name        = azurerm_resource_group.prod_rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = true
  soft_delete_retention_days = 90
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Purge"
    ]

    key_permissions = [
      "Get",
      "List"
    ]
  }
}





# Create the staging resource group
resource "azurerm_resource_group" "staging_rg" {
  name     = var.staging_resource_group_name
  location = var.resource_location
}
resource "azurerm_storage_container" "staging_container" {
  name               = var.terraform_state_statging_container_name
  storage_account_id = azurerm_storage_account.tfstate_storage.id
  # Changed access_type to "private" to make the container private
  container_access_type = "private"
}

# Create key vault for staging
resource "azurerm_key_vault" "staging_kv" {
  name                       = "${var.staging_resource_group_name}-kv"
  location                   = var.resource_location
  resource_group_name        = azurerm_resource_group.staging_rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = true
  soft_delete_retention_days = 90
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Purge"
    ]

    key_permissions = [
      "Get",
      "List"
    ]
  }
}

# Create managent azure identity 
resource "azurerm_user_assigned_identity" "management_identity" {
  name                = "id-application-identity"
  resource_group_name = azurerm_resource_group.bootstrap_rg.name
  location            = var.resource_location
}
# Grant access to the management identity to the key vaults
resource "azurerm_key_vault_access_policy" "prod_kv_access_policy" {
  key_vault_id = azurerm_key_vault.prod_kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.management_identity.principal_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Purge"
  ]

  key_permissions = [
    "Get",
    "List"
  ]
}
resource "azurerm_key_vault_access_policy" "staging_kv_access_policy" {
  key_vault_id = azurerm_key_vault.staging_kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.management_identity.principal_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Purge"
  ]

  key_permissions = [
    "Get",
    "List"
  ]
}
# Grant Storage Blob Data Contributor role to the current user for the tfstate storage account


resource "azurerm_role_assignment" "tfstate_prod_storage_contributor" {
  scope                = azurerm_storage_account.tfstate_storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.management_identity.principal_id
}
# For local development
resource "azurerm_role_assignment" "tfstate_local_storage_contributor" {
  scope                = azurerm_storage_account.tfstate_storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}


# Used 2 differnet methods of access
# AZURE RBAC (Role-Based Access Control) is a method of access control that allows you to assign roles to users, groups, and applications. It is a more flexible and granular way of controlling access to Azure resources. In this case, we are using AZURE RBAC to grant the management identity and the current user access to the tfstate storage account.
# LEGACY ACCESS POLICIES is a method of access control that allows you to assign permissions to users, groups, and applications. It is a more rigid and less flexible way of controlling access to Azure resources. In this case, we are using LEGACY ACCESS POLICIES to grant the management identity access to the key vaults.
# I DID THIS FOR LEARNING PURPOSE



resource "azurerm_role_assignment" "tfstate_github_actions_contributor" {
  scope                = azurerm_storage_account.tfstate_storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.github_actions_principal_id
}