import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List,Tuple,Literal
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
from pydantic import BaseModel,Field
from langchain_core.output_parsers import StrOutputParser
logger = logging.getLogger(__name__)

class RouterModelOutput(BaseModel):

    method: Literal[
            "hybrid_search_tool", 
            "local_graph_search_tool", 
            "global_graph_search_tool", 
            "unrelated_or_conversational"
        ] = Field(
            description="Target retrieval pipeline based on the user intent."
        )
    standalone_query: str = Field(
            description="The rephrased, self-contained search query. If the input is conversational or already clear, return it cleanly without adding conversational text or greetings."
        )
class AgentService:
    """Service layer for AI Agent RAG queries and chat history management."""
    def __init__(
        self,
        llm_singleton=llm_singleton,
        vector_service=vector_service,
        graph_service=graph_service,
    ):
        self.llm_singleton = llm_singleton
        self.vector_service = vector_service
        self.graph_service = graph_service
        self._llm = None
        self._quick_model = None
        self._agent_executor = None
        self._general_llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = self.llm_singleton.get_llm()
        return self._llm

    @property
    def quick_model(self):
        if self._quick_model is None:
            self._quick_model = self.llm_singleton.get_quick_anwser_model()
        return self._quick_model

    @property
    def agent_executor(self):
        if self._agent_executor is None:
            tools = self.create_agent_tools(
                graph_service=self.graph_service,
                vector_service=self.vector_service,
            )
            system_prompt_template ="""You are an expert, professional Regulatory Assistant.
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

            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt_template),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            agent = create_tool_calling_agent(self.llm, tools, prompt)
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                max_iterations=4,
                early_stopping_method="force",
                verbose=True,
                return_intermediate_steps=True,
            )
        return self._agent_executor
      

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

    def _refactor_user_query(self, query: str,history: List[Dict[str, Any]]) -> tuple[str,str]:
        # Use the quick model to refactor the user's query
        prompt_template = ChatPromptTemplate.from_messages([
            ("system",
            "You are an intent classifier and query optimizer for a RAG system.\n"
            "Your tasks:\n"
            "1. **method**: Classify the user intent into one of the available tools:\n"
            "   - 'hybrid_search_tool': Specific factual, document-based, legal, domain, or entity questions.\n"
            "   - 'local_graph_search_tool': Specific entity relationships or graph links.\n"
            "   - 'global_graph_search_tool': Broad summaries or overall repository overviews.\n"
            "   - 'unrelated_or_conversational': Simple greetings (e.g. 'hi', 'thanks', 'how can you help me') or non-document questions.\n"
            "2. **standalone_query**: Rephrase the user input using conversation history if history is available into a clear, standalone search query.\n"
            "   - CRITICAL: Do NOT answer the question, greet the user, or add commentary in 'standalone_query'. Just output the optimized search text."
            ),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{user_input}")                        
        ])
        structured_model=self.quick_model.with_structured_output(RouterModelOutput)
        chain = prompt_template | structured_model
        response = chain.invoke({
            "history": history,
            "user_input": query
        })
        logger.debug(f"Refactored query output from model : {response.method}, {response.standalone_query}")
        return response.method, response.standalone_query

    
    def _hybrid_search_tool(self, query: str) -> Dict[str, Any]:
        """PRIMARY TOOL. Use this first for all factual, legal, or document-specific questions."""
        result = vector_service.hybrid_search(query)
        return {
        "context": result.get("context", ""),
        "sources": result.get("sources", []),
        "graph_context": result.get("graph_context", []),
        "hybrid_search_score": result.get("hybrid_search_score", 0)
            }

    def _extract_string_from_output(self, output: Any) -> str:
        """Extracts a string from the model's output, handling different output formats."""
        logger.debug(f"Extracting string from model output: {output}")
        if isinstance(output, list):
            agent_output = "\n".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in output
            )
        else:
            agent_output = str(output)
        return agent_output
    

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
        try:
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
        except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to persist initial user query state: {str(e)}")
                raise e 
            
        #  Search history 
        history = (
            db.session.query(Conversation)
            .filter_by(chat_id=chat.chat_id)
            .order_by(Conversation.created_at.desc())
            .limit(10)  
            .all()
        )[::-1]

        # Convert the history to langchain history format
        langchain_history = []
        for msg in history:
            if msg.role.value == ConversationRole.USER:
                langchain_history.append(HumanMessage(content=msg.content))
            elif msg.role.value == ConversationRole.ASSISTANT:
                langchain_history.append(AIMessage(content=msg.content))
        
        extracted_sources = []
        extracted_graph_context = []
        confidence_score = None
        routed_method = None
        intermediate_steps=[]
        try:
            # Refactor user input with lighweight and fast model
            routed_method, refactored_query=self._refactor_user_query(query, langchain_history)
            match routed_method:
                case "hybrid_search_tool":
                    logger.info("Routing to hybrid_search_tool based on query and history.")
                    hybrid_result = self._hybrid_search_tool(refactored_query)
                    extracted_sources.extend(hybrid_result.get("sources", []))
                    extracted_graph_context.extend(hybrid_result.get("graph_context", []))
                    confidence_score = hybrid_result.get("hybrid_search_score", 0)
                    # LLm invoke 
                    synthesis_prompt = ChatPromptTemplate.from_messages([
                    ("system", "Answer the user question accurately using strictly the provided context.\nContext:\n{context}"),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("user", "{user_input}")
                ])
                    synthesis_chain = synthesis_prompt | self.quick_model
                    try:
                        synthesis_response = synthesis_chain.invoke({
                            "context": hybrid_result.get("context", ""),
                            "chat_history": langchain_history,
                            "user_input": refactored_query
                        })
                        # LLM output
                        agent_output_data = getattr(synthesis_response, "content", "I'm sorry, I couldn't process an answer.")
                        agent_output = self._extract_string_from_output(agent_output_data)
                    except Exception as e:
                        logger.error(f"Error in synthesis chain: {str(e)}")
                        agent_output = "I'm sorry, I encountered an error generating a response. Please try again."
                case "unrelated_or_conversational":
                    logger.info("Routing to unrelated_or_conversational based on query and history.")
                    conv_prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are a helpful, professional,document QA assistant.."
                         "For greetings or questions about your capabilities, answer politely and explain that you assist with analyzing the uploaded repository documents."
                        "For general domain or technical questions not present in the documents (e.g., weather, third-party pricing, general tech facts), politely inform the user that you can only answer questions based on the provided documents."
                        "Do not answer questions that require specific document context or legal advice or private or internal data. "
                        "If the question is unrelated to the provided context, respond politely and inform the user that you cannot provide an answer.",
                        ),
                        MessagesPlaceholder(variable_name="chat_history"),
                        ("user", "{user_input}")
                    ])
                    try:
                        conv_chain = conv_prompt | self.quick_model
                        response = conv_chain.invoke({
                            "chat_history": langchain_history,
                            "user_input": refactored_query
                        })
                        agent_output_data = getattr(response, "content", "I'm sorry, I couldn't process an answer.")

                        agent_output = self._extract_string_from_output(agent_output_data)
                        confidence_score = 1.0

                    except Exception as e:
                        logger.error(f"Error in conversational chain: {str(e)}")
                        agent_output = "I'm sorry, I encountered an error generating a response. Please try again."
                        confidence_score = 0.0
                case _:
                            logger.info(f"Routing to agent_executor based on query and history. Routed method: {routed_method}")
                    # Call the ai agent_executor to process the query with tools and context
                            try:
                                agent_response = self.agent_executor.invoke({"input": refactored_query, "chat_history": langchain_history})
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
                                                

                            for action, tool_output in intermediate_steps:
                                artifact = None
                                if isinstance(tool_output, tuple) and len(tool_output) == 2:
                                    _, artifact = tool_output
                                if isinstance(tool_output, dict):
                                    artifact = tool_output
                                if isinstance(artifact, dict):
                                    extracted_sources.extend(artifact.get("sources", []))
                                    extracted_graph_context.extend(artifact.get("graph_context", []))
        except Exception as e:
                logger.error(f"Error during query processing: {str(e)}")
                agent_output = "I'm sorry, I encountered an error processing your request. Please try again."
                # intermediate_steps = []
                confidence_score = 0.0

                
                
                
        # Remove duplicate sources from the intermediate_steps as agent can call multiple tools
        deduplicated_sources=[]
        if extracted_sources:
            seen_sources=set()
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
        else:
            # Fallback heuristic: Higher if tools retrieved context, lower if direct generation
            confidence_score= confidence_score is None and 0.85 if intermediate_steps else 0.60
        answer_text = re.sub(r"CONFIDENCE_SCORE:\s*[0-9\.]+", "", agent_output).strip() if routed_method =="local_graph_search" or routed_method == "global_graph_search" else agent_output.strip()

        try:
            # Persist Assistant Response
            rag_source = {
                "confidence_score": round(confidence_score, 2),
                "sources": deduplicated_sources,
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
            db.session.flush()

            # Return Response Matching Exact API Schema
            created_at_iso = (
                assistant_conv.created_at.isoformat()
                if assistant_conv.created_at
                else datetime.now(timezone.utc).isoformat()
            )
            db.session.commit()

            return {
                "chat_id": str(chat.chat_id),
                "conversation_id": str(assistant_conv.conversation_id),
                "role": "ASSISTANT",
                "content": answer_text,
                "created_at": created_at_iso,
                "rag_source": rag_source,
            }   
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to persist assistant response: {str(e)}")
            raise Exception("Failed to save assistant response", 500)

    

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

# TODO: ADD PAGINATION AND LIMITING FOR LARGE HISTORIES
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
