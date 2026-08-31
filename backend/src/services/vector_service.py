# backend/services/vector_service.py
import time
from typing import List, Optional, Dict, Any
import logging
import uuid
from weaviate.classes.config import Configure, Property, DataType, Tokenization
from weaviate.classes.query import Filter, MetadataQuery
from config.vector_db import weaviate_client
from config.llm import llm_singleton
from core.exceptions import AppError, VectorStoreError
from google.genai.errors import ClientError
from config.database import db
from models.document import Document, DocumentStatus
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
logger = logging.getLogger(__name__)

try:
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    ResourceExhausted = None

try:
    from langchain_google_genai._common import GoogleGenerativeAIError
except ImportError:
    GoogleGenerativeAIError = Exception
RETRYABLE_EXCEPTIONS = tuple(
    exc for exc in (ClientError, ResourceExhausted,GoogleGenerativeAIError) if exc is not None
)
class VectorService:
    """Service layer for managing document vector embeddings in Weaviate."""

    COLLECTION_NAME = "DocumentChunk"

    def __init__(self, client_singleton=weaviate_client, llm_config=llm_singleton,db=db):
        self.client_singleton = client_singleton
        self.llm_config = llm_config
        self.db = db
        self._schema_initialized = False

    def _get_client(self):
        try:
            return self.client_singleton.get_client()
        except Exception as e:
            raise VectorStoreError(f"Failed to connect to Weaviate: {str(e)}") from e

    def init_schema(self) -> None:
        """
        Ensures the 'DocumentChunk' collection schema exists in Weaviate.
        Creates collection with custom vector indexing if not present.
        """
        logger.info("Initializing Weaviate schema for DocumentChunk collection.")
        properties = [
            # Core Foreign Key & Navigation
            Property(
                name="document_id",
                data_type=DataType.TEXT,
                index_filterable=True,
                index_searchable=False,
                tokenization=Tokenization.FIELD,  # Preserves exact UUID matching
            ),
            Property(
                name="chunk_id",
                data_type=DataType.TEXT,
                index_filterable=True,
                index_searchable=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="text",
                data_type=DataType.TEXT,
                index_filterable=True,
                index_searchable=True,
                tokenization=Tokenization.WORD,
            ),
            # Hybrid Search Boosters (BM25)
            Property(
                name="circular_number",
                data_type=DataType.TEXT,
                index_filterable=True,
                index_searchable=True,
                tokenization=Tokenization.FIELD,  # Keeps codes like "CIRC-2024/012" intact
            ),
            Property(
                name="title",
                data_type=DataType.TEXT,
                index_filterable=True,
                index_searchable=True,
                tokenization=Tokenization.WORD,
            ),
            # Pre-Filtering Attributes
            Property(
                name="category",
                data_type=DataType.TEXT,
                index_filterable=True,
                index_searchable=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="publication_date",
                data_type=DataType.TEXT,
                index_filterable=True,
            ),
            # Direct Citation Attribute
            Property(
                name="page_number",
                data_type=DataType.INT,
                index_filterable=True,
            ),
        ]
        try:
            if not self._schema_initialized:
                client = self._get_client()
                if not client.collections.exists(self.COLLECTION_NAME):
                    client.collections.create(
                        name=self.COLLECTION_NAME,
                        properties=properties,
                        vectorizer_config=Configure.Vectorizer.none(),
                    )
                self._schema_initialized = True
                logger.info("Weaviate schema initialized successfully.")

        except Exception as e:
            raise VectorStoreError(
                f"Failed to initialize Weaviate schema: {str(e)}"
            ) from e
    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        stop=stop_after_attempt(6),
        before_sleep=lambda retry_state: logger.warning(
            f"Gemini API rate limit hit (429). Retrying attempt {retry_state.attempt_number} "
            f"in {retry_state.next_action.sleep:.1f} seconds..."
        ),
    )
    def embed_batch_with_retry(self, embedding_model, batch_texts: List[str]):
        return embedding_model.embed_documents(batch_texts)

    def store_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        vectors: Optional[List[List[float]]] = None,
        title: Optional[str] = None,
        circular_number: Optional[str] = None,
        publication_date: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """
        Batch stores document chunks with vector embeddings in Weaviate.
        """
        if not chunks:
            return 0

        try:
            self.init_schema()
            client = self._get_client()
            collection = client.collections.get(self.COLLECTION_NAME)
            logger.info(
                f"Storing {len(chunks)} chunks for document {document_id} in Weaviate."
            )

            if vectors is None:
                logger.info(
                    "No pre-computed vectors provided. Generating embeddings using Gemini."
                )
                embedding_model = self.llm_config.get_embedding_model()
                texts = [chunk.get("text", "") for chunk in chunks]
                batch_size = 50
                vectors = []
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i : i + batch_size]
                    # batch_vectors = embedding_model.embed_documents(batch_texts)
                    batch_vectors = self.embed_batch_with_retry(embedding_model, batch_texts)
                    vectors.extend(batch_vectors)
                    time.sleep(4.5)  # Optional: slight delay to avoid rate limits
                logger.info(f"Generated {len(vectors)} embeddings for the chunks.")

            if len(vectors) != len(chunks):
                raise VectorStoreError("Mismatch between number of vectors and chunks.")

            with collection.batch.dynamic() as batch:
                logger.info("Starting batch storage in Weaviate.")
                for idx, chunk in enumerate(chunks):
                    properties = {
                        "document_id": str(document_id),
                        "chunk_id": str(chunk.get("chunk_id", idx)),
                        "text": str(chunk.get("text", "")),
                        "page_number": int(chunk.get("page_number", 1)),
                        "category": str(category) if category else None,
                        "title": str(title) if title else None,
                        "circular_number": str(circular_number)
                        if circular_number
                        else None,
                        "publication_date": str(publication_date)
                        if publication_date
                        else None,
                    }
                    batch.add_object(
                        properties=properties,
                        vector=vectors[idx],
                    )

            failed_objects = collection.batch.failed_objects
            if failed_objects:
                logger.error(
                    f"Failed to insert {len(failed_objects)} chunks in Weaviate: {failed_objects[0]}"
                )
                self.delete_document_chunks(document_id)
                raise VectorStoreError(
                    f"Failed to store chunks in Weaviate. {len(failed_objects)} objects failed."
                )

            logger.info(
                f"Successfully stored {len(chunks)} chunks for document {document_id} in Weaviate."
            )
            return len(chunks)

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                f"Failed to store chunks in Weaviate: {str(e)}"
            ) from e

    def hybrid_search(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        limit: int = 15,
        document_ids: Optional[List[str]] = None,
        alpha: float = 0.25,
    ) -> List[Dict[str, Any]]:
        """
        Performs hybrid search (sparse BM25 + dense vector) on DocumentChunk.
        """
        try:
            self.init_schema()
            client = self._get_client()
            collection = client.collections.get(self.COLLECTION_NAME)

            if query_vector is None:
                embedding_model = self.llm_config.get_embedding_model()
                query_vector = embedding_model.embed_query(query)

            filters = None
            if document_ids:
                filters = Filter.by_property("document_id").contains_any(
                    [str(doc_id) for doc_id in document_ids]
                )
            # Overfetch to ensure we have enough results after filtering out inactive documents
            overfetch_limit = limit if document_ids else limit * 3
            results = collection.query.hybrid(
                query=query,
                vector=query_vector,
                alpha=alpha,
                limit=overfetch_limit,
                filters=filters,
                return_metadata=MetadataQuery(score=True, explain_score=True),
            )
            if not results.objects:
                return {"context": "No relevant text passages found.", "sources": [], "graph_context": []}
            # Filter to only return the chunks that the document ID is active in the DB
            doc_ids=list({
            str(obj.properties.get("document_id")) 
            for obj in results.objects
              if obj.properties.get("document_id") 
            })
            docs = (
                self.db.session.query(Document)
                .filter(Document.document_id.in_(doc_ids))
                .filter(Document.status == DocumentStatus.ACTIVE_COMPLETED)
                .all()
            )
            docs_maps = {str(doc.document_id): doc for doc in docs}
            sources = []
            text_passages = []

            for obj in results.objects:
                props = obj.properties
                doc_id = str(props.get("document_id"))
                if doc_id not in docs_maps:
                    continue  # Skip chunks from inactive documents
                text = props.get("text", "")
                sources.append( 
                    {
                        "document_id": props.get("document_id", "unknown"),
                        "document": props.get("filename", "document.pdf"),
                        "title": props.get("title", "Untitled Document"),
                        "page": props.get("page_number", 1),
                        "snippet": text[:200] + "..." if len(text) > 200 else text,
                    }
                )

                text_passages.append(
                    f"[Doc: {props.get('title')} | Page {props.get('page_number')}]\nExcerpt: \"{text}\""
                )
            # TO ADD :  Rreanker model
            context_text = "### RETRIEVED TEXT PASSAGES\n" + "\n\n".join(text_passages)

            return {"context": context_text, "sources": sources, "graph_context": []}

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(f"Hybrid search failed: {str(e)}") from e

    def vector_search(
        self,
        query_vector: List[float],
        limit: int = 5,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs dense vector search (near_vector) on DocumentChunk.
        """
        try:
            self.init_schema()
            client = self._get_client()
            collection = client.collections.get(self.COLLECTION_NAME)

            filters = None
            if document_ids:
                filters = Filter.by_property("document_id").contains_any(
                    [str(doc_id) for doc_id in document_ids]
                )

            results = collection.query.near_vector(
                near_vector=query_vector,
                limit=limit,
                filters=filters,
                return_metadata=MetadataQuery(distance=True, certainty=True),
            )

            data = []
            for obj in results.objects:
                props = obj.properties
                data.append(
                    {
                        "chunk_id": props.get("chunk_id"),
                        "document_id": props.get("document_id"),
                        "text": props.get("text"),
                        "page_number": props.get("page_number"),
                        "category": props.get("category"),
                        "publication_date": props.get("publication_date"),
                        "title": props.get("title"),
                        "circular_number": props.get("circular_number"),
                        "distance": getattr(obj.metadata, "distance", None),
                        "certainty": getattr(obj.metadata, "certainty", None),
                    }
                )
            return data

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(f"Vector search failed: {str(e)}") from e

    def delete_document_chunks(self, document_id: str) -> bool:
        """
        Deletes all vector chunks matching document_id.
        """
        try:
            self.init_schema()
            client = self._get_client()
            collection = client.collections.get(self.COLLECTION_NAME)
            logger.info(
                f"Deleting all chunks for document {document_id} from Weaviate."
            )
            collection.data.delete_many(
                where=Filter.by_property("document_id").equal(str(document_id))
            )
            logger.info(
                f"Successfully deleted all chunks for document {document_id} from Weaviate."
            )
            return True

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                f"Failed to delete vector chunks for document {document_id}: {str(e)}"
            ) from e

    def get_chunks_by_ids(self, chunk_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetches chunks from Weaviate matching a list of chunk_ids."""
        # TO ADD :ONLY RETURN THE CHUNKS THAT THE DOCUMENT ID IS ACTIVE IN TEH DB
        if not chunk_ids:
            return {}
        client = self._get_client()
        collection = client.collections.get(self.COLLECTION_NAME)
        response = collection.query.fetch_objects(
            filters=Filter.by_property("chunk_id").contains_any(chunk_ids),
            limit=len(chunk_ids),
        )

        chunk_map = {}
        for obj in response.objects:
            props = obj.properties
            chunk_map[props["chunk_id"]] = {
                "text": props.get("text", ""),
                "document_id": props.get("document_id", "Unknown"),
                "page_number": props.get("page_number", "N/A"),
                "circular_number": props.get("circular_number", "None"),
            }
        return chunk_map

    def get_chunks_by_document_id(self, document_id: str) -> List[str]:
        """Fetches all chunks from Weaviate for a given document_id."""
        client = self._get_client()
        collection = client.collections.get(self.COLLECTION_NAME)
        response = collection.query.fetch_objects(
            filters=Filter.by_property("document_id").equal(str(document_id))
        )

        chunks = []
        for obj in response.objects:
            props = obj.properties
            chunks.append(props.get("chunk_id"))
        return chunks


vector_service = VectorService()
