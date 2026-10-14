import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class AzureBlobClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AzureBlobClient, cls).__new__(cls, *args, **kwargs)
            cls._instance._client = None
        return cls._instance

    def get_client(self) -> BlobServiceClient:
        if self._client is None:
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            if not account_name:
                raise ValueError(
                    "AZURE_STORAGE_ACCOUNT_NAME environment variable is not set"
                )
            account_url = f"https://{account_name}.blob.core.windows.net"
            credential = DefaultAzureCredential()
            
            self._client = BlobServiceClient(
                account_url=account_url, 
                credential=credential
            )
        return self._client


azure_blob_client = AzureBlobClient()
