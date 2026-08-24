import os
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
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            if not connection_string:
                raise ValueError(
                    "AZURE_STORAGE_CONNECTION_STRING environment variable is not set"
                )
            self._client = BlobServiceClient.from_connection_string(connection_string)
        return self._client


azure_blob_client = AzureBlobClient()
