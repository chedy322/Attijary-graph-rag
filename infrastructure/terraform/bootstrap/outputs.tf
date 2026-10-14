output "AZURE_STAGING_KEY_VAULT_URI"{
    value= azurerm_key_vault.staging_kv.vault_uri
    description = "Azure Staging Key Vault URI"
}

output "AZURE_PROD_KEY_VAULT_URI"{
    value= azurerm_key_vault.prod_kv.vault_uri
    description = "Azure Prod Key Vault URI"
}