from flask import Blueprint, request, jsonify
from core.middleware import require_auth
from services.auth_service import auth_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("", methods=["POST", "OPTIONS"])
@auth_bp.route("/", methods=["POST", "OPTIONS"])
@require_auth
def authenticate():
    result = auth_service.sync_user()
    return jsonify(result.model_dump(mode="json")), 200
