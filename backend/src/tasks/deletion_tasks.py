# backend/tasks/deletion_tasks.py
from celery import shared_task

from config.celery_app import celery_client
import logging
from services.document_service import document_service
from services.vector_service import vector_service
from services.graph_service import graph_service
from services.storage_service import storage_service
from config.database import db
from models.document import Document
celery = celery_client.get_app()
logger = logging.getLogger(__name__)

@shared_task(name="tasks.run_cascading_deletion", bind=True,
             max_retries=3, default_retry_delay=60)  
def run_cascading_deletion(self, document_id: str):
    """
    Celery task: Idempotent cascading deletion of all document data.

    Steps (to be implemented):
        1. Delete all vectors from Weaviate for this document_id.
        2. Delete all nodes/edges from Neo4j for this file_id.
        3. Delete the blob from Azure Storage.
        4. Hard-delete the Postgres document row.

    Args:
        document_id: UUID string of the document to delete.
    """
   
    logger.info(
        f"[deletion_tasks] run_cascading_deletion triggered for document_id={document_id}"
    )
    try:
        # First query the database to get the document's file_path before deletion
        document=document_service.get_document_by_id(document_id)
        if not document:
            logger.warning(
                f"[deletion_tasks] Document with id={document_id} not found in database.Failure to delete document."
            )
            return {
                "status": "warning",
                "message": f"Document with id={document_id} not found in database.Failed to delete document.",
            }
        file_path = document.file_path
        # Fetch all the chunks associated with the document_id from weviate to pass them to the graph service for deletion
        chunk_ids = vector_service.get_chunks_by_document_id(document_id)

        # Delete all nodes/edges from Neo4j for this document_id
        if chunk_ids:
            graph_service.delete_by_chunk_ids(chunk_ids)

        # Delete all vectors from Weaviate for this document_id
        vector_service.delete_document_chunks(document_id)
        # Delete the blob from Azure Storage
        if file_path:
            storage_service.delete_document(file_path)

        # Hard-delete the Postgres document row last
        document_service.delete_document(document_id)
        logger.info(f"[deletion_tasks] Successfully completed deletion for document_id={document_id}")
        return {
            "status": "success",
            "message": f"Successfully completed deletion for document_id={document_id}",
            "document_id": document_id,
            
        }
    except Exception as e:
        logger.error(
            f"[deletion_tasks] Error during cascading deletion for document_id={document_id}: {str(e)}"
        )
