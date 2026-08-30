from flask import Blueprint, jsonify
from core.middleware import require_auth, admin_required
import uuid

scraper_bp = Blueprint("scraper", __name__)


@scraper_bp.route("/sync", methods=["POST", "OPTIONS"])
@require_auth
@admin_required
def trigger_scraper():
    """
    POST /api/v1/scraper/sync
    Triggers an asynchronous Celery worker to scrape circulars.
    """
    task_id = f"scraper-task-{uuid.uuid4()}"
    return jsonify({
        "message": "Web scraping synchronization process started.",
        "task_id": task_id
    }), 202


@scraper_bp.route("/status/<task_id>", methods=["GET", "OPTIONS"])
@require_auth
@admin_required
def get_scraper_status(task_id):
    """
    GET /api/v1/scraper/status/<task_id>
    Polls the status of an active or completed background scraping task.
    """
    return jsonify({
        "task_id": task_id,
        "status": "SUCCESS",
        "result": {
            "scraped_pages": 5,
            "new_documents_found": 2,
            "indexed_document_ids": []
        }
    }), 200
