
from core.middleware import require_auth, admin_required

from flask import Blueprint, jsonify, request

from services.audit_service import audit_service
audit_bp = Blueprint("audit", __name__)

@audit_bp.route("/logs", methods=["GET"])
@require_auth
@admin_required
def get_audit_logs():
    """
    GET /api/v1/audits/logs
    Returns a list of audit logs for the authenticated user.
    """
    page=request.args.get("page", 1, type=int)
    limit=request.args.get("limit", 10, type=int)   
    offset = (page - 1) * limit
    result = audit_service.find_all_logs(limit=limit, offset=offset)
    logs= [obj.model_dump(mode="json") for obj in result]
    return jsonify({
        "status": "success",
        "data": logs,
        "meta": {
            "page": page,
            "limit": limit,
            "total": len(result),
            "total_pages": (len(result) + limit - 1) // limit,
        },
    }), 200