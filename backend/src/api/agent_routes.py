import json

from flask import Blueprint, request, jsonify, g, Response, stream_with_context
from core.middleware import require_auth, admin_required
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

    @stream_with_context
    def generate():
        yield json.dumps({"type": "ready", "data": None}) + "\n"
        try:
            for event in agent_service.stream_query(
                clerk_user_id=g.user_id,
                query=str(query).strip(),
                chat_id=chat_id,
            ):
                yield json.dumps(event, separators=(",", ":")) + "\n"
        except Exception as error:
            yield json.dumps(
                {"type": "error", "data": str(error)},
                separators=(",", ":"),
            ) + "\n"

    return Response(
        generate(),
        status=200,
        mimetype="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


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
    agent_service.delete_chat(clerk_user_id=g.user_id, chat_id=chat_id)
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
    result = agent_service.get_document_lineage(
        document_id=document_id
    )

    return jsonify({
        "root_document_id": str(document_id),
        "nodes": result.get("nodes", []),
        "edges": result.get("edges", [])
    }), 200
