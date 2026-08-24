import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from models.document import DocumentStatus
from config.database import db
from config.llm import llm_singleton
from core.exceptions import AppError
from models.user import User
from models.chat import Chat
from models.conversation import Conversation, ConversationRole
from models.document import Document
from services.vector_service import vector_service
from typing import List
from langchain.agents import create_agent
from langchain.tools import tool
from services.graph_service import GraphService, graph_service
from services.vector_service import VectorService

import asyncio

logger = logging.getLogger(__name__)


class AgentService:
    """Service layer for AI Agent RAG queries and chat history management."""

    def __init__(
        self,
        llm=llm_singleton,
        vector_service=vector_service,
        graph_service=graph_service,
    ):
        self.llm = llm.get_llm()
        self.vector_service = (vector_service,)
        self.graph_service = graph_service
        self.tools = self.create_agent_tools(
            graph_service=graph_service, vector_service=vector_service
        )
        self.agent_executor = create_agent(model=self.llm, tools=self.tools)

    def create_agent_tools(
        self, graph_service: GraphService, vector_service: VectorService
    ):
        """Creates tool bindings injected with active service instances."""

        @tool
        def local_graph_search_tool(entities: List[str]) -> str:
            """Search Neo4j and Weaviate for entity relationships and relevant document passages."""
            result = graph_service.local_graph_search(entities, vector_service)
            return result["context"]

        @tool
        def global_graph_search_tool(query: str) -> str:
            """Search top-level community summaries in the knowledge graph for broader context."""
            result = graph_service.global_graph_search(query)
            return result["context"]

        @tool
        def hybrid_search_tool(query: str) -> str:
            """Perform dense vector + BM25 keyword search across all vector documents."""
            result = vector_service.hybrid_search(query)
            return result["context"]

        return [local_graph_search_tool, global_graph_search_tool, hybrid_search_tool]

    def _get_user(self, clerk_user_id: str) -> User:
        """Fetch User by clerk_id or auto-create if missing."""
        user = db.session.query(User).filter_by(clerk_id=clerk_user_id).first()
        if not user:
            raise Exception("User not found", 404)
        return user

    def process_query(
        self,
        clerk_user_id: str,
        query: str,
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute RAG flow for a user query:
        1. Resolve user & chat session
        2. Persist USER conversation
        3. Hybrid vector search
        4. LLM context generation
        5. Persist ASSISTANT conversation with rag_source
        """
        if not query or not query.strip():
            raise Exception("Query string cannot be empty.", 400)

        user = self._get_user(clerk_user_id)

        # 1. Chat Session Check & Creation
        if not chat_id:
            title = query.strip()[:50]
            chat = Chat(
                user_id=user.user_id,
                title=title,
            )
            db.session.add(chat)
            db.session.flush()
        else:
            try:
                chat_uuid = uuid.UUID(chat_id)
            except ValueError:
                raise Exception("Invalid chat_id format", 400)

            chat = (
                db.session.query(Chat)
                .filter_by(chat_id=chat_uuid, user_id=user.user_id)
                .first()
            )
            if not chat:
                raise Exception("Chat session not found", 404)

        # 2. Persist User Message
        user_conv = Conversation(
            chat_id=chat.chat_id,
            role=ConversationRole.USER,
            content=query,
        )
        db.session.add(user_conv)
        db.session.commit()

        # 3. Hybrid Search Retrieval
        retrieved_chunks = []
        try:
            retrieved_chunks = vector_service.hybrid_search(query=query)
            print(retrieved_chunks)
        except Exception as e:
            logger.warning(
                f"Hybrid search failed, continuing without vector context: {str(e)}"
            )

        # Hydrate document metadata from Postgres
        # only return the document with the status ACTIVE_COMPLETED, and ignore the others
        sources = []
        doc_ids = list(
            {
                chunk["document_id"]
                for chunk in retrieved_chunks
                if chunk.get("document_id")
            }
        )
        doc_map = {}
        if doc_ids:
            try:
                doc_uuids = [uuid.UUID(did) for did in doc_ids if did]
                # Document Id should be indexed in the database, but we will filter by ACTIVE_COMPLETED status to ensure we only return valid documents
                docs = (
                    db.session.query(Document)
                    .filter(Document.document_id.in_(doc_uuids))
                    .filter(Document.status == DocumentStatus.ACTIVE_COMPLETED)
                    .all()
                )
                doc_map = {str(d.document_id): d for d in docs}
            except Exception as e:
                logger.warning(f"Failed to fetch document metadata: {str(e)}")

        max_score = 0.0
        for chunk in retrieved_chunks:
            did = chunk.get("document_id")
            doc = doc_map.get(did)
            doc_title = doc.title if doc else "Regulatory Document"
            doc_file = (
                doc.file_path.rsplit("/", 1)[-1]
                if doc and doc.file_path
                else "document.pdf"
            )
            score = chunk.get("score") or 0.0
            if score > max_score:
                max_score = score
            sources.append(
                {
                    "document_id": did or "",
                    "document": doc_file,
                    "title": doc_title,
                    "page": chunk.get("page_number", 1),
                    "snippet": chunk.get("text", ""),
                }
            )

        # Calculate confidence score (normalized 0-100)
        confidence_score = (
            round(min(100.0, max(50.0, max_score * 100)), 1) if max_score > 0 else 85.0
        )
        # Add reranker model
        # 4. Fetch Previous History & Format LLM Prompt
        history = (
            db.session.query(Conversation)
            .filter_by(chat_id=chat.chat_id)
            .order_by(Conversation.created_at.asc())
            .all()
        )

        history_text = (
            "\n".join([f"{c.role.value}: {c.content}" for c in history[:-1]])
            if len(history) > 1
            else ""
        )  # exclude last inserted user query to avoid duplicate

        context_snippets = "\n\n".join(
            [
                f"[Source: {s['title']}, Page {s['page']}]\n{s['snippet']}"
                for s in sources
            ]
        )

        system_prompt = f"""You are a professional Regulatory Assistant.
Answer the user's query accurately based on the provided document context and conversation history.
If the context does not contain the answer, rely on regulatory principles while noting limitations. Always cite document names and page numbers when available.

--- CONTEXT SNIPPETS ---
{context_snippets if context_snippets else 'No context snippets available.'}

--- CONVERSATION HISTORY ---
{history_text if history_text else 'No previous conversation.'}

--- USER QUERY ---
{query}

Answer:"""

        # Call LLM
        try:
            llm = llm_singleton.get_llm()
            llm_response = llm.invoke(system_prompt)
            content_str = llm_response.content
            if isinstance(content_str, list):
                # Extract 'text' from block list: [{'type': 'text', 'text': '...'}]
                text_blocks = []
                for item in content_str:
                    if isinstance(item, str):
                        text_blocks.append(item)
                    elif isinstance(item, dict) and item.get("type") == "text":
                        text_blocks.append(item.get("text", ""))
                answer_text = "\n".join(text_blocks)
            elif not isinstance(content_str, str):
                answer_text = str(content_str)

        except Exception as e:
            logger.error(f"LLM execution failed: {str(e)}")
            answer_text = "I'm sorry, I encountered an error generating a response. Please try again."

        # 5. Persist Assistant Response
        rag_source = {
            "confidence_score": confidence_score,
            "sources": sources,
            "graph_context": [],
        }

        assistant_conv = Conversation(
            chat_id=chat.chat_id,
            role=ConversationRole.ASSISTANT,
            content=answer_text,
            rag_source=rag_source,
        )
        db.session.add(assistant_conv)
        db.session.commit()

        # 6. Return Response Matching Exact API Schema
        created_at_iso = (
            assistant_conv.created_at.isoformat()
            if assistant_conv.created_at
            else datetime.now(timezone.utc).isoformat()
        )

        return {
            "chat_id": str(chat.chat_id),
            "conversation_id": str(assistant_conv.conversation_id),
            "role": "ASSISTANT",
            "content": answer_text,
            "created_at": created_at_iso,
            "rag_source": rag_source,
        }

    def fetch_chats(self, clerk_user_id: str) -> List[Dict[str, Any]]:
        """Fetch all chat sessions for a user."""
        user = self._get_user(clerk_user_id)
        chats = (
            db.session.query(Chat)
            .filter_by(user_id=user.user_id)
            .order_by(Chat.created_at.desc())
            .all()
        )
        return [
            {
                "chat_id": str(chat.chat_id),
                "title": chat.title,
                "created_at": chat.created_at.isoformat() if chat.created_at else None,
            }
            for chat in chats
        ]

    def fetch_conversation_by_chat_id(
        self, clerk_user_id: str, chat_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch all conversations for a specific chat session."""
        user = self._get_user(clerk_user_id)
        try:
            chat_uuid = uuid.UUID(chat_id)
        except ValueError:
            raise Exception("Invalid chat_id format", 400)

        chat = (
            db.session.query(Chat)
            .filter_by(chat_id=chat_uuid, user_id=user.user_id)
            .first()
        )
        if not chat:
            raise Exception("Chat session not found", 404)

        conversations = (
            db.session.query(Conversation)
            .filter_by(chat_id=chat.chat_id)
            .order_by(Conversation.created_at.asc())
            .all()
        )
        return {
            "chat_id": chat.chat_id,
            "title": chat.title,
            "messages": [
                {
                    "conversation_id": str(conv.conversation_id),
                    "role": conv.role.value,
                    "content": conv.content,
                    "created_at": conv.created_at.isoformat()
                    if conv.created_at
                    else None,
                    "rag_source": conv.rag_source,
                }
                for conv in conversations
            ],
        }


agent_service = AgentService()
