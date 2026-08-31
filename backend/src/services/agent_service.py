import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List,Tuple
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
# from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
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
        self.vector_service = vector_service
        self.graph_service = graph_service
        self.tools = self.create_agent_tools(
            graph_service=graph_service, vector_service=vector_service)

        # Improved, highly directive System Prompt
        system_prompt_template = """You are an expert, professional Regulatory Assistant.
        Your primary role is to answer user queries accurately based on the provided document context, knowledge graph data, and conversation history.

        Key Instructions:
        1. BEFORE calling any tool, check if the retrieved text from previous tool steps already contains the necessary details.
        2. If a tool call returns clear, relevant excerpt text, DO NOT run additional tool searches. Formulate your final response immediately.
        3. Call at most ONE search tool per query unless the initial search yields zero context or explicitly fails.
        4. Prefer 'hybrid_search_tool' for specific factual or legal questions.
        5. Always cite your sources using document names and page numbers (e.g., "According to [Title], Page [X]").
        6. Rely strictly on the provided tool context. If the answer is unavailable, state this clearly.
        7. Append a confidence tag at the very end of your response formatted exactly as:
        CONFIDENCE_SCORE: <float between 0.00 and 1.00>
        """

        # Setup the modern Tool Calling Agent prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Initialize the Agent and Executor
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            max_iterations=4,
            early_stopping_method="force",
            verbose=True, 
            return_intermediate_steps=True
        )

    def create_agent_tools(
        self, graph_service: GraphService, vector_service: VectorService
    ):
        """Creates tool bindings using artifacts to separate LLM text context from rich metadata."""

        @tool
        def local_graph_search_tool(entities: List[str]) ->  Dict[str, Any]:
            """FALLBACK ONLY. Use ONLY when hybrid_search fails or when explicit entity relationships are asked."""
            result = graph_service.local_graph_search(entities, vector_service)
            return {
                "context": result.get("context", ""),
                "sources": result.get("sources", []),
                "graph_context": result.get("graph_context", [])
            }

        @tool
        def global_graph_search_tool(query: str) -> Dict[str, Any]:
            """Search top-level community summaries in the knowledge graph for broader context."""
            result = graph_service.global_graph_search(query)
            return {
        "context": result.get("context", ""),
        "sources": result.get("sources", []),
        "graph_context": result.get("graph_context", [])
    }

        @tool
        def hybrid_search_tool(query: str) -> Dict[str, Any]:
            """PRIMARY TOOL. Use this first for all factual, legal, or document-specific questions."""
            result = vector_service.hybrid_search(query)
            return {
        "context": result.get("context", ""),
        "sources": result.get("sources", []),
        "graph_context": result.get("graph_context", [])
    }

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

        # Chat Session Check & Creation
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

        # Persist User Message
        user_conv = Conversation(
            chat_id=chat.chat_id,
            role=ConversationRole.USER,
            content=query,
        )
        db.session.add(user_conv)
        db.session.commit()

        #  Search history 
        history = (
            db.session.query(Conversation)
            .filter_by(chat_id=chat.chat_id)
            .order_by(Conversation.created_at.asc())
            .all()
        )

        # Convert the history to langchain history format
        langchain_history = []
        for msg in history[:-1]:
            if msg.role.value == ConversationRole.USER:
                langchain_history.append(HumanMessage(content=msg.content))
            elif msg.role.value == ConversationRole.ASSISTANT:
                langchain_history.append(AIMessage(content=msg.content))
        # Call the ai agent_executor to process the query with tools and context
        try:
            agent_response = self.agent_executor.invoke({"input": query, "chat_history": langchain_history})
            # print(f"Agent response: {agent_response}")
            raw_output = agent_response.get("output", "I'm sorry, I couldn't process an answer. ")
            # print(f"Agent output: {raw_output}")
            if isinstance(raw_output, list):
                # Joins text blocks from content blocks
                agent_output = "\n".join([
                    block.get("text", "") for block in raw_output 
                    if isinstance(block, dict) and block.get("type") == "text"
                ])
            elif isinstance(raw_output, dict):
                agent_output = raw_output.get("text", str(raw_output))
            else:
                agent_output = str(raw_output)
            intermediate_steps = agent_response.get("intermediate_steps", [])
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            agent_output = "I'm sorry, I encountered an error generating a response. Please try again."
            intermediate_steps = []
        # 
        extracted_sources = []
        extracted_graph_context = []
        for action, tool_output in intermediate_steps:
            artifact = None
            if isinstance(tool_output, tuple) and len(tool_output) == 2:
                _, artifact = tool_output
            if isinstance(tool_output, dict):
                artifact = tool_output
            if isinstance(artifact, dict):
                extracted_sources.extend(artifact.get("sources", []))
                extracted_graph_context.extend(artifact.get("graph_context", []))

        # Remove duplicate sources from the intermediate_steps as agent cab call multiple tools
        seen_sources=set()
        deduplicated_sources=[]
        for src in extracted_sources:
            doc_id=src.get("document_id") or f"{src.get('title')}_{src.get('page_number')}"
            if doc_id not in seen_sources:
                deduplicated_sources.append(src)
                seen_sources.add(doc_id)

    
        confidence_match = re.search(r"CONFIDENCE_SCORE:\s*([0-9\.]+)", agent_output)
        if confidence_match:
            try:
                confidence_score = float(confidence_match.group(1))
            except ValueError:
                confidence_score = 0.70
            # Strip tag so users don't see raw metadata
            answer_text = re.sub(r"CONFIDENCE_SCORE:\s*[0-9\.]+", "", agent_output).strip()
        else:
            # Fallback heuristic: Higher if tools retrieved context, lower if direct generation
            confidence_score = 0.85 if intermediate_steps else 0.60
            answer_text = agent_output.strip()



        # Persist Assistant Response
        rag_source = {
            "confidence_score": round(confidence_score, 2),
            "sources": extracted_sources,
            "graph_context": extracted_graph_context,
        }
        # Store the assistant's response in the database
        assistant_conv = Conversation(
            chat_id=chat.chat_id,
            role=ConversationRole.ASSISTANT,
            content=answer_text,
            rag_source=rag_source,
        )
        db.session.add(assistant_conv)
        db.session.commit()

        # Return Response Matching Exact API Schema
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

    def delete_chat(self, clerk_user_id: str, chat_id: str) -> Dict[str, Any]:
        """Delete a specific chat session and its associated conversations."""
        user = self._get_user(clerk_user_id)
        try:
            chat_uuid = uuid.UUID(chat_id)
        except ValueError:
            raise Exception("Invalid chat_id format", 400)
        try:
            chat = (
                db.session.query(Chat)
                .filter_by(chat_id=chat_uuid, user_id=user.user_id)
                .first()
            )
            if not chat:
                raise Exception("Chat session not found", 404)

            # Delete associated conversations first due to foreign key constraints
            db.session.query(Conversation).filter_by(chat_id=chat.chat_id).delete()
            db.session.delete(chat)
            db.session.commit()
            return {"message": "Chat session and its conversations deleted successfully."}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting chat session: {str(e)}")
            raise Exception("Failed to delete chat session", 500)
    def get_document_lineage(
    self, document_id: str,
) -> Dict[str, Any]:
        source_chunks = self.vector_service.get_chunks_by_document_id(document_id)
        if not source_chunks:
            return {"root_document_id": document_id, "nodes": [], "edges": []}

        cypher_query = """
        MATCH (s:Entity)-[r]->(o:Entity)
        WHERE r.chunk_id IN $chunk_ids
        RETURN 
            s.name AS source,
            s.type AS source_type,
            type(r) AS relation,
            r.chunk_id AS chunk_id,
            o.name AS target,
            o.type AS target_type
        """
        records, _, _ = self.graph_service.graph.execute_query(cypher_query, {"chunk_ids": source_chunks})

        if not records:
            return {"root_document_id": document_id, "nodes": [], "edges": []}

        # Collect all unique chunk_ids attached to connected target nodes
        found_chunk_ids = set()
        for rec in records:
            if rec["chunk_id"]:
                found_chunk_ids.add(rec["chunk_id"])

        # ------------------------------------------------------------------
        # STEP 3: Query Weaviate to map returned chunk_ids to target document_ids
        # ------------------------------------------------------------------
        chunk_to_doc_map = self.vector_service.get_chunks_by_ids(list(found_chunk_ids))
        # Expected returned mapping format: 
        # { "chunk_123": {"document_id": "a9988776...", "title": "Circular N° 2022-12"} }

        nodes_dict = {}
        edges_set = set()

        # Add root node explicitly
        root_title = chunk_to_doc_map.get(source_chunks[0], {}).get("title", "Root Document")
        nodes_dict[document_id] = {
            "id": document_id,
            "label": root_title,
            "type": "Document"
        }

        for rec in records:
            c_id = rec["chunk_id"]
            target_doc_info = chunk_to_doc_map.get(c_id)

            if target_doc_info:
                target_doc_id = target_doc_info["document_id"]
                target_title = target_doc_info.get("title", "Untitled Document")

                # Add connected document node
                if target_doc_id not in nodes_dict:
                    nodes_dict[target_doc_id] = {
                        "id": target_doc_id,
                        "label": target_title,
                        "type": "Document"
                    }

                # Avoid self-referencing document edges
                if document_id != target_doc_id:
                    edges_set.add((document_id, target_doc_id, rec["relation"]))

        formatted_edges = [
            {"source": src, "target": tgt, "relationship": rel}
            for src, tgt, rel in edges_set
        ]

        return {
            "root_document_id": document_id,
            "nodes": list(nodes_dict.values()),
            "edges": formatted_edges
        }
        
        

agent_service = AgentService()
