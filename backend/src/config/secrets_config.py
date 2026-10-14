import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import logging
logger = logging.getLogger(__name__)
class SecretsAppConfig:
    @staticmethod
    def load_secrets_from_cloud_to_local(url_key_vault: str) -> str:
        """
        Load secrets from Azure Key Vault to local environment variables.
        Retrieve a secret from environment variables.
        """
        flask_env = os.getenv("FLASK_ENV")
        if not flask_env:
            raise ValueError("FLASK_ENV is not set in environment variables.")
        if flask_env not in ["development", "staging", "production"]:
            raise ValueError("FLASK_ENV is not a valid value.")
        if flask_env == "production" or flask_env == "staging":
            logger.info(f"Loading secrets from Azure Key Vault: {url_key_vault}")
            secret_value = os.getenv(url_key_vault)
            if secret_value is None:
                raise ValueError(f"Secret '{url_key_vault}' not found in environment variables.")
            try:
                client = SecretClient(vault_url=url_key_vault, credential=DefaultAzureCredential())
                
                # Pull ALL secrets into os.environ at startup
                for secret_property in client.list_properties_of_secrets():
                    if secret_property.enabled:
                        url_key_vault = secret_property.name
                        secret_value = client.get_secret(url_key_vault).value
                        env_key = url_key_vault.replace("-", "_")
                        
                        # Populates os.getenv(...) dynamically across the entire Flask app
                        os.environ.setdefault(env_key, secret_value)
            except Exception as e:
                logger.warning(f"Key Vault bulk load warning: {e}")