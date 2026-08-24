
output "AZURE_STORAGE_ACCOUNT_NAME" {
  value       = azurerm_storage_account.storage.name
  description = "Azure Storage Account Name"
}

output "AZURE_BLOB_CONTAINER_NAME" {
  value       = azurerm_storage_container.container.name
  description = "Azure Blob Container Name"
}

output "AZURE_STORAGE_ACCOUNT_KEY" {
  value       = azurerm_storage_account.storage.primary_access_key
  description = "Azure Storage Account Key"
  sensitive   = true # Hides the value in the terminal during apply
}

output "AZURE_STORAGE_CONNECTION_STRING" {
  value       = azurerm_storage_account.storage.primary_connection_string
  description = "Azure Storage Connection String"
  sensitive   = true
}
