# backend/tasks/deletion_tasks.py
from config.celery_app import celery_client

celery = celery_client.get_app()


@celery.task(name="tasks.run_cascading_deletion", bind=True)
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
    # TODO: implement cascading deletion
    print(
        f"[deletion_tasks] run_cascading_deletion triggered for document_id={document_id}"
    )
