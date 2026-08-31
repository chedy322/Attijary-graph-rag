# backend/api/document_routes.py
from flask import Blueprint, request, jsonify, g
from core.middleware import require_auth, admin_required
from core.exceptions import AppError
from services.document_service import document_service
from services.storage_service import storage_service
from tasks.indexing_tasks import run_indexing_pipeline
from tasks.deletion_tasks import run_cascading_deletion
import uuid
from models.document import DocumentStatus

document_bp = Blueprint("documents", __name__)
# Admin can get,edit,delete,index any document even if it s not his document, but the user can only get his own document.


# ── GET / ─────────────────────────────────────────────────────────────────────
@document_bp.route("/", methods=["GET"])
@require_auth
@admin_required
def list_documents():
    """Paginated list of documents with optional status filter."""
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    status = request.args.get("status", None, type=str)

    items, total = document_service.get_documents(page=page, limit=limit, status=status)

    return jsonify(
        {
            "status": "success",
            "data": [doc.to_dict() for doc in items],
            "meta": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
            },
        }
    ), 200


# ── POST /upload-url ──────────────────────────────────────────────────────────
# Fix error in the date it s the published date and not the uplaod date
@document_bp.route("/upload-url", methods=["POST"])
@require_auth
@admin_required
def get_upload_url():
    """Create a DB record (PENDING_UPLOAD) and return an Azure SAS upload URL."""
    body = request.get_json(silent=True) or {}
    clerk_user_id = g.user_id
    filename = body.get("filename")
    title = body.get("title")
    number = body.get("number")
    category = body.get("category")
    # date     = body.get("date")

    if not filename or not title:
        raise AppError("filename, title are required", 400)
    doc_id = uuid.uuid4()
    # generate the file path from the hosted azure
    azure_blob_path, file_url = storage_service.calculate_file_path(
        clerk_user_id, doc_id, filename
    )
    document = document_service.create_document(
        document_id=doc_id,
        file_path=file_url,
        filename=filename,
        title=title,
        # date=date,
        uploaded_by_user_id=clerk_user_id,
        number=number,
        category=category,
    )

    sas_url = storage_service.generate_upload_sas(azure_blob_path)

    return jsonify(
        {
            "status": "success",
            "data": {
                "document": document.to_dict(),
                "upload_url": sas_url,
            },
        }
    ), 201


# ── POST /<document_id>/index ─────────────────────────────────────────────────
# This gets triggered when a user wants to index a document. It sets the status to PROCESSING and enqueues the indexing pipeline.
@document_bp.route("/<uuid:document_id>/index", methods=["POST"])
@require_auth
@admin_required
def index_document(document_id):
    """Set status → PROCESSING and enqueue the indexing pipeline."""
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise AppError("Document not found", 404)
    # Check if the document isn t already being processed or indexed
    if document.status == DocumentStatus.ACTIVE_COMPLETED:
        return jsonify(
            {
                "status": "skipped",
                "message": f"Document '{document_id}' is already fully indexed.",
                "document_id": str(document_id),
            }
        ), 200

    if document.status == DocumentStatus.PROCESSING:
        raise AppError("Document is currently being processed", 400)

    document_service.update_status(document_id, DocumentStatus.PROCESSING)

    task = run_indexing_pipeline.delay(
        str(document_id),
        document.title,
        document.number,
        str(document.date),
        document.category,
        document.file_path,
    )

    return jsonify(
        {
            "status": "success",
            "data": {
                "document_id": str(document_id),
                "task_id": task.id,
                "message": "Indexing pipeline enqueued",
            },
        }
    ), 202


# ── GET /<document_id> ────────────────────────────────────────────────────────
@document_bp.route("/<uuid:document_id>", methods=["GET"])
@require_auth
def get_document(document_id):
    """Fetch a single document by UUID."""
    if g.get(
        "user_role"
    ) != "ADMIN" and not document_service.get_document_by_id_and_clerk_user_id(
        document_id, g.user_id
    ):
        raise AppError("Unauthorized access to this document", 403)
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise AppError("Document not found", 404)

    return jsonify(
        {
            "status": "success",
            "data": document.to_dict(),
        }
    ), 200


# ── DELETE /<document_id> ─────────────────────────────────────────────────────
@document_bp.route("/<uuid:document_id>", methods=["DELETE"])
@require_auth
@admin_required
def delete_document(document_id):
    """Set status → PENDING_DELETE and enqueue the cascading deletion task."""
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise AppError("Document not found", 404)
    if document.status == DocumentStatus.PENDING_DELETE:
        return jsonify(
            {
                "status": "skipped",
                "message": f"Document '{document_id}' is already marked for deletion.",
                "document_id": str(document_id),
            }
        ), 200
    document_service.update_status(document_id, "PENDING_DELETE")
    task = run_cascading_deletion.delay(str(document_id))

    return jsonify(
        {
            "status": "success",
            "data": {
                "document_id": str(document_id),
                "task_id": task.id,
                "message": "Deletion pipeline enqueued",
            },
        }
    ), 202
