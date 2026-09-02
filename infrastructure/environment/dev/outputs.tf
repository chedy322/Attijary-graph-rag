output "AZURE_STORAGE_ACCOUNT_NAME" {
  value       = module.storage_bucket.AZURE_STORAGE_ACCOUNT_NAME
  description = "Azure Storage Account Name"
}

output "AZURE_BLOB_CONTAINER_NAME" {
  value       = module.storage_bucket.AZURE_BLOB_CONTAINER_NAME
  description = "Azure Blob Container Name"
}

output "AZURE_STORAGE_ACCOUNT_KEY" {
  value       = module.storage_bucket.AZURE_STORAGE_ACCOUNT_KEY
  description = "Azure Storage Account Key"
  sensitive   = true # Must match sensitive flag from module
}

output "AZURE_STORAGE_CONNECTION_STRING" {
  value       = module.storage_bucket.AZURE_STORAGE_CONNECTION_STRING
  description = "Azure Storage Connection String"
  sensitive   = true # Must match sensitive flag from module
}

# output "public_ip_address" {
#   value = module.virtual_machine.public_ip_address
# }
