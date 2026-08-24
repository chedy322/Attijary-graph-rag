from flask import Blueprint, request, jsonify, g
from core.middleware import require_auth
from core.exceptions import AppError
from services.agent_service import agent_service

agent_bp = Blueprint("agent", __name__)


@agent_bp.route("/query", methods=["POST"])
@require_auth
def query_agent():
    """
    POST /api/v1/agent/query
    Executes AI Agent RAG flow with session management.
    """
    body = request.get_json(silent=True) or {}
    query = body.get("query")
    chat_id = body.get("chat_id")

    if not query or not str(query).strip():
        raise Exception("Query is required in request body.", 400)

    result = agent_service.process_query(
        clerk_user_id=g.user_id,
        query=str(query).strip(),
        chat_id=chat_id,
    )

    return jsonify(result), 200


@agent_bp.route("/chats", methods=["GET"])
@require_auth
def list_chats():
    """
    GET /api/v1/agent/chats
    Returns a list of chat sessions for the authenticated user.
    """
    result = agent_service.fetch_chats(clerk_user_id=g.user_id)
    return jsonify(result), 200


@agent_bp.route("/chats/<chat_id>/messages", methods=["GET"])
@require_auth
def get_chat_messages(chat_id):
    """
    GET /api/v1/agent/chats/<chat_id>/messages
    Returns all messages for a specific chat session.
    """
    result = agent_service.fetch_conversation_by_chat_id(
        clerk_user_id=g.user_id, chat_id=chat_id
    )
    return jsonify(result), 200
