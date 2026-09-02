# backend/services/storage_service.py
import os
from datetime import datetime, timedelta, timezone

from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from config.azure_blob import azure_blob_client
from core.exceptions import AppError
import logging
logger = logging.getLogger(__name__)

class StorageService:
    blobServiceClient = None
    containerClient = None
    accountName = None
    containerName = None

    def __init__(self):
        """Initialize the StorageService with an AzureBlobClient instance."""
        container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")
        account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        if not all([container_name, account_name, account_key]):
            raise AppError(
                "Azure storage configuration is incomplete. "
                "Ensure AZURE_BLOB_CONTAINER_NAME, AZURE_STORAGE_ACCOUNT_NAME, "
                "and AZURE_STORAGE_ACCOUNT_KEY are set.",
                500,
            )
        self.blobServiceClient = azure_blob_client.get_client()
        self.containerClient = self.blobServiceClient.get_container_client(
            container_name
        )
        self.accountName = account_name
        self.containerName = container_name
        self.account_key = account_key

    """Handles all Azure Blob Storage operations."""

    def calculate_file_path(self, userId, documentId, filename: str) -> str:
        # userId is from clerk_user_id and not the user_id form the db
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        blobName = f"{userId}/{documentId}.{extension}"
        fileUrl = f"https://{self.accountName}.blob.core.windows.net/{self.containerName}/{blobName}"

        return (blobName, fileUrl)

    def generate_upload_sas(self, file_url: str) -> str:
        """
        Generate a pre-signed SAS URL granting WRITE access for 1 hour.
        The frontend uploads the file directly to Azure using this URL.

        Args:
            file_path: The blob path inside the container, e.g. 'documents/<uuid>.pdf'

        Returns:
            A fully-qualified SAS URL string.
        """
        try:
            start_time = datetime.now(timezone.utc)- timedelta(minutes=15)  # Start time is 5 minutes in the past to account for clock skew
            expire_time = start_time + timedelta(hours=1)

            # FIX: Translated Node.js SAS generation into standard Python azure-storage-blob implementation
            sas_token = generate_blob_sas(
                account_name=self.accountName,
                container_name=self.containerName,
                blob_name=file_url,
                account_key=self.account_key,
                permission=BlobSasPermissions(write=True, create=True),
                start=start_time,
                expiry=expire_time,
            )

            # Construct the full URL with the generated SAS token
            blob_client = self.containerClient.get_blob_client(blob=file_url)
            sas_url = f"{blob_client.url}?{sas_token}"

            return sas_url

        except AppError:
            raise
        except Exception as e:
            raise AppError(f"Failed to generate SAS URL: {str(e)}", 500) from e

    # Delete a document from Azure Blob Storage
    def delete_document(self, file_url: str) -> None:
        """
        Delete a document from Azure Blob Storage.

        Args:
            file_url: The blob path inside the container, e.g. 'documents/<uuid>.pdf'
        """
        try:
            blob_client = self.containerClient.get_blob_client(blob=file_url)
            blob_client.delete_blob()
        except Exception as e:
            logger.error(f"[storage_service] Error deleting blob {file_url}: {str(e)}")
            raise AppError(f"Failed to delete document: {str(e)}", 500) from e

    def restore_deleted_document(self, file_url: str) -> None:
        """
        Restore a deleted document from Azure Blob Storage.

        Args:
            file_url: The blob path inside the container, e.g. 'documents/<uuid>.pdf'
        """
        try:
            blob_client = self.containerClient.get_blob_client(blob=file_url)
            blob_client.undelete_blob()
        except Exception as e:
            raise AppError(f"Failed to restore document: {str(e)}", 500) from e


storage_service = StorageService()
