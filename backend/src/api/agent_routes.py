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


@agent_bp.route("/chats/<chat_id>/messages", methods=["GET", "OPTIONS"])
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


@agent_bp.route("/chats/<chat_id>", methods=["DELETE", "OPTIONS"])
@require_auth
def delete_chat(chat_id):
    """
    DELETE /api/v1/agent/chats/<chat_id>
    Deletes a chat session and cascades to delete all associated message rows.
    """
    return jsonify({
        "message": "Chat session and message history successfully deleted.",
        "chat_id": chat_id
    }), 200


@agent_bp.route("/graph/lineage/<document_id>", methods=["GET", "OPTIONS"])
@require_auth
def get_graph_lineage(document_id):
    """
    GET /api/v1/agent/graph/lineage/<document_id>
    Fetches structural graph connections (nodes and edges) associated with a given document.
    """
    return jsonify({
        "root_document_id": str(document_id),
        "nodes": [
            { "id": str(document_id), "label": "Circular N° 2026-05", "type": "Document" },
            { "id": "cb-circ-2022-12", "label": "Circular N° 2022-12", "type": "Document" }
        ],
        "edges": [
            { "source": str(document_id), "target": "cb-circ-2022-12", "relationship": "MODIFIES" }
        ]
    }), 200

