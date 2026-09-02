
resource "azurerm_storage_account" "storage" {
  name                     = var.resource_name
  resource_group_name      = var.resource_group_name
  location                 =var.resource_location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  public_network_access_enabled = true
  allow_nested_items_to_be_public = true
  shared_access_key_enabled     = true
  identity {
        type = "SystemAssigned"
    }
    blob_properties {
        cors_rule {
            allowed_headers    = ["*"]
            allowed_methods    = ["GET", "PUT", "OPTIONS", "POST", "HEAD"]
            allowed_origins    = ["*"]
            exposed_headers    = ["*"]
            max_age_in_seconds = 3600
        }
  }

}

resource "time_sleep" "wait_for_storage" {
  depends_on      = [azurerm_storage_account.storage]
  create_duration = "30s"
}

resource "azurerm_storage_container" "container"{
  name                  = "documentsuploads"
  storage_account_id    = azurerm_storage_account.storage.id
  # Changed access_type to "blob" to allow public read access to blobs in the container
  container_access_type = "blob"
  # depends_on = [time_sleep.wait_for_storage]
}

# resource "azurerm_role_assignment" "app_storage_access" {
#   scope                = azurerm_storage_container.container.id
#   role_definition_name = "Storage Blob Data Contributor"
#   # principal_id         = azurerm_storage_account.storage.identity[0].principal_id
# }
