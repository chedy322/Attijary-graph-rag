# backend/tasks/indexing_tasks.py
import tempfile

import tempfile
import os
from config.celery_app import celery_client
from flask import current_app
from helper.text_extractor import extract_text_from_pdf
from helper.chunker import chunk_text
from celery import shared_task
from celery.utils.log import get_task_logger
from services.vector_service import vector_service
from services.document_service import document_service
from models.document import DocumentStatus
from pathlib import Path
from services.graph_service import graph_service
from config.azure_blob import azure_blob_client
from urllib.parse import urlparse

celery = celery_client.get_app()
logger = get_task_logger(__name__)


# @celery.task(name="tasks.run_indexing_pipeline", bind=True)
@shared_task(name="tasks.run_indexing_pipeline", bind=True)
def run_indexing_pipeline(
    self,
    document_id: str,
    title: str,
    circular_number: str,
    publication_date: str,
    category: str,
    file_path: str,
):
    """
    Celery task: AI ingestion pipeline for a single document.

    Steps (to be implemented):
        1. Download blob from Azure Storage.
        2. Chunk the document via LangChain (10% overlap).
        3. Embed chunks via Gemini → store in Weaviate.
        4. Extract entities/edges via LLM → store in Neo4j.
        5. Update document status to ACTIVE/COMPLETED (or FAILED).

    Args:
        document_id: UUID string of the document to index.
        title: The title of the document.
        circular_number: The circular number of the document.
        publication_date: The publication date of the document.
        category: The category of the document.
    """
    try:
        logger.info(
            f"[indexing_tasks] run_indexing_pipeline triggered for document_id={document_id}"
        )
        # 1. Download blob from Azure Storage
        # Extract the extension from the file_path
        file_extension = Path(file_path).suffix.lower()
        # Extract the blob path
        parsed_path = urlparse(file_path).path.lstrip("/")
        container_name = current_app.config.get(
            "AZURE_BLOB_CONTAINER_NAME"
        ) or os.getenv("AZURE_BLOB_CONTAINER_NAME")
        if container_name and parsed_path.startswith(f"{container_name}/"):
            blob_path = parsed_path.split(f"{container_name}/", 1)[1]
        else:
            blob_path = parsed_path.split("/", 1)[-1]

        blob_service_client = azure_blob_client.get_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_path
        )
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            logger.info(
                f"[indexing_tasks] Downloading blob for document_id={document_id} to temporary file {temp_file.name}"
            )
            try:
                # Download the file from the blob storage to the temporary file
                download_stream = blob_client.download_blob()
                temp_file.write(download_stream.readall())
                temp_file.flush()
                temp_file.close()
                logger.info(
                    f"[indexing_tasks] Finished downloading blob for document_id={document_id} to temporary file {temp_file.name}"
                )
                # 2. Chunk the document via LangChain (10% overlap).
                pages_array = extract_text_from_pdf(temp_file.name)
            finally:
                # Ensure the temporary file is deleted after processing
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)
                    logger.info(
                        f"[indexing_tasks] Temporary file {temp_file.name} deleted for document_id={document_id}"
                    )
                else:
                    logger.warning(
                        f"[indexing_tasks] Temporary file {temp_file.name} not found for deletion for document_id={document_id}"
                    )
        # pages_array = extract_text_from_pdf(file_path)
        if not pages_array:
            logger.warning(
                f"[indexing_tasks] No text extracted from document_id={document_id}. Cannot proceed with indexing."
            )
            raise Exception(
                f"No text extracted from document_id={document_id}. Cannot proceed with indexing."
            )
        chunks = chunk_text(pages_array, max_tokens=600, overlap_tokens=100)
        if not chunks:
            logger.warning(
                f"[indexing_tasks] No chunks generated from document_id={document_id}. Cannot proceed with indexing."
            )
            raise Exception(
                f"No chunks generated from document_id={document_id}. Cannot proceed with indexing."
            )
        # 3. Embed chunks via Gemini → store in Weaviate.
        stored_count = vector_service.store_chunks(
            document_id=document_id,
            chunks=chunks,
            title=title,
            circular_number=circular_number,
            publication_date=publication_date,
            category=category,
        )
        logger.info(
            f"[indexing_tasks] Successfully stored {stored_count} chunks in Weaviate for document_id={document_id}"
        )
        # 4. Extract entities/edges via LLM → store in Neo4j.
        graph_results = graph_service.index_graph_pipeline(chunks)
        logger.info(
            f"[indexing_tasks] Successfully extracted and stored graph data for document_id={document_id}. Extracted {len(graph_results)} chunks with entities/relationships."
        )

        # 5. Update document status to ACTIVE/COMPLETED (or FAILED).
        document_service.update_status(
            document_id=document_id, new_status=DocumentStatus.ACTIVE_COMPLETED
        )
        logger.info(
            f"[indexing_tasks] Document {document_id} indexing pipeline completed successfully. Status updated to ACTIVE/COMPLETED."
        )
        return {
            "status": "SUCCESS",
            "document_id": document_id,
            "chunks_indexed": stored_count,
        }
    except Exception as e:
        logger.error(
            f"[indexing_tasks] Error in run_indexing_pipeline for document_id={document_id}: {str(e)}",
            exc_info=True,
        )
        # Mark the document as FAILED in database here
        try:
            vector_service.delete_document_chunks(document_id)
        except Exception as delete_error:
            logger.error(
                f"[indexing_tasks] Failed to delete chunks for document_id={document_id} after indexing failure: {str(delete_error)}",
                exc_info=True,
            )
        # Mark the document as FAILED in database here
        try:
            document_service.update_status(
                document_id=document_id, new_status=DocumentStatus.FAILED
            )
        except Exception as status_error:
            logger.error(
                f"[indexing_tasks] Failed to update status to FAILED for document_id={document_id}: {str(status_error)}",
                exc_info=True,
            )

        raise e
