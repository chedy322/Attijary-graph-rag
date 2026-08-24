from collections import defaultdict
from html import entities
import logging
from typing import List, Dict, Any, Tuple
import concurrent
from config.llm import llm_singleton
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from concurrent.futures import ThreadPoolExecutor
from config.neo4j_db import neo4j_client
from services.vector_service import VectorService
import networkx as nx
import numpy as np
import logging

logger = logging.getLogger(__name__)


# Define the structure to feed the llm output with
class RelationshipTriplet(BaseModel):
    subject: str = Field(description="The source entity name, e.g., 'Circular 102'")
    subject_type: str = Field(
        description="Must be one of: ORGANIZATION, LAW, PROCEDURE, DEPARTMENT, REGULATORY_CONCEPT, DOCUMENT"
    )
    relation: str = Field(
        description="Must be one of: MODIFIES, REFERENCES, BELONGS_TO, GOVERNS, ISSUED_BY"
    )
    object: str = Field(
        description="The target entity name, e.g., 'Treasury Department'"
    )
    object_type: str = Field(
        description="Must be one of: ORGANIZATION, LAW, PROCEDURE, DEPARTMENT, REGULATORY_CONCEPT, DOCUMENT"
    )


class ExtractionResponse(BaseModel):
    triplets: List[RelationshipTriplet] = Field(
        description="List of all extracted triplets found in the text."
    )


class QueryEntitiesResponse(BaseModel):
    entities: List[str] = Field(
        description="List of entity names, document titles, or concepts extracted from the user query."
    )


class GraphService:
    def __init__(self, llm_config=llm_singleton, graph_client=neo4j_client):
        # self.graph_client = graph_client
        # Get the llm client
        self.llm_config = llm_config
        self.graph = graph_client.get_driver()
        self.base_llm = llm_config.get_llm()
        self.structured_llm = self.base_llm.with_structured_output(ExtractionResponse)

    # def get_graph_data(self, query):
    #     # Implement the logic to fetch data from the graph database using the graph_client
    #     return self.graph_client.execute_query(query)
    def extract_entities_and_relationships(
        self, chunk: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract entities and relationships from the provided chunks using an LLM.

        """
        logger.info(
            f"[graph_service] Extracting entities and relationships for chunk_id={chunk.get('chunk_id', 'unknown')}"
        )

        text_content = chunk.get("text", "")

        if not text_content.strip():
            logger.warning(
                f"[graph_service] Empty text content for chunk_id={chunk.get('chunk_id', 'unknown')}. Skipping extraction."
            )
            return []
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert legal and regulatory data analyst.
            Analyze the text provided by the user and extract all key entities and their exact relationships.

            CRITICAL RULES:
            1. Entity types MUST strictly be: ORGANIZATION, LAW, PROCEDURE, DEPARTMENT, REGULATORY_CONCEPT, DOCUMENT.
            2. Relationship types MUST strictly be: MODIFIES, REFERENCES, BELONGS_TO, GOVERNS, ISSUED_BY.
            3. If a circular updates or alters another document, use the 'MODIFIES' relation.

            ENTITY STANDARDIZATION RULES (MANDATORY):
            - Remove leading articles (e.g., output "Treasury Department", NOT "The Treasury Department").
            - Remove legal suffixes unless crucial (e.g., "Apple", NOT "Apple Inc.").
            - Resolve acronyms if the full name is present in the text (e.g., Use "Central Bank", NOT "CB").
            - Use Title Case for all entity names.
            - Strip all dates or revision numbers from document names unless it is part of the official title.
            """,
                ),
                ("human", "{text}"),
            ]
        )

        try:
            chain = prompt | self.structured_llm

            # Execute and get a type-safe Pydantic object back automatically
            response: ExtractionResponse = chain.invoke({"text": text_content})

            results = []
            for t in response.triplets:
                item = t.model_dump()
                item["chunk_id"] = chunk.get("chunk_id", "unknown")
                results.append(item)
            logger.info(
                f"[graph_service] Extracted {len(results)} triplets for chunk_id={chunk.get('chunk_id', 'unknown')}"
            )
            return results

        except Exception as e:
            raise Exception(f"Error in LLM processing: {str(e)}")

    def remove_duplicates(
        self, extracted_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate entities and relationships using vector similarity.
        """
        logger.info(
            f"[graph_service] Removing duplicates from extracted data. Initial count: {len(extracted_data)}"
        )
        if not extracted_data:
            logger.info(
                f"[graph_service] No data to deduplicate for chunk_id={extracted_data.get('chunk_id', 'unknown')}. Returning empty list."
            )
            return []

        embeddings_model = self.llm_config.get_embedding_model()

        # 1. Gather all unique entity names from both subject and object fields
        unique_entities = set()
        for t in extracted_data:
            unique_entities.add(t["subject"])
            unique_entities.add(t["object"])

        unique_entities = list(unique_entities)

        # 2. Get embeddings for all unique entities in one batch
        try:
            embeddings = embeddings_model.embed_documents(unique_entities)
        except Exception as e:
            logger.error(
                f"[graph_service] Error generating embeddings for deduplication: {str(e)}"
            )
            return extracted_data  # Return original data if embeddings fail

        # 3. Find duplicates using cosine similarity
        # We will create a mapping from "Duplicate Name" -> "Master Name"
        entity_mapping = {}
        threshold = 0.95

        # Convert to numpy array for fast math
        embeddings_matrix = np.array(embeddings)

        # Calculate dot product (cosine similarity since OpenAI embeddings are normalized)
        similarity_matrix = np.dot(embeddings_matrix, embeddings_matrix.T)

        for i in range(len(unique_entities)):
            if unique_entities[i] in entity_mapping:
                continue  # Already mapped to a master entity

            # Find all entities similar to this one (including itself)
            similar_indices = np.where(similarity_matrix[i] > threshold)[0]

            # The first entity we find becomes the "Master"
            master_entity = unique_entities[i]

            for j in similar_indices:
                duplicate_entity = unique_entities[j]
                entity_mapping[duplicate_entity] = master_entity

        # 4. Rewrite the triplets using the master mapping
        deduplicated_data = []
        # Keep track of unique triplets so we don't add the same edge twice
        seen_edges = set()

        for t in extracted_data:
            standardized_subject = entity_mapping[t["subject"]]
            standardized_object = entity_mapping[t["object"]]

            # Avoid self-referencing relationships if subject and object merged into the same entity
            if standardized_subject == standardized_object:
                continue

            edge_signature = (
                f"{standardized_subject}-{t['relation']}-{standardized_object}"
            )

            if edge_signature not in seen_edges:
                seen_edges.add(edge_signature)
                # Create a new dict with updated names
                clean_triplet = t.copy()
                clean_triplet["subject"] = standardized_subject
                clean_triplet["object"] = standardized_object
                deduplicated_data.append(clean_triplet)
        logger.info(
            f"[graph_service] Deduplication complete. Final count: {len(deduplicated_data)}"
        )
        return deduplicated_data

    def create_community_group(
        self, extracted_data: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Create community grouping of the entities and relationships using graph algorithms.
        Returns a tuple of (nodes, edges) where nodes are the unique entities and edges are the relationships.
        """
        if not extracted_data:
            logger.info(
                f"[graph_service] No data to create community groups for chunk_id={extracted_data.get('chunk_id', 'unknown')}."
            )
            return [], {}
        # Initialize a graph using NetworkX
        G = nx.Graph()

        for triplet in extracted_data:
            subject = triplet["subject"]
            object_ = triplet["object"]
            G.add_edge(subject, object_, relation=triplet["relation"])

        community_to_entities = {}
        entity_to_community = {}
        # Perform Laieden algorithm to detect communities [{node1, node2, ...}, {node3, node4, ...}, ...]
        communities = list(nx.community.louvain_communities(G))
        # Map each community to its entities
        for idx, community_nodes in enumerate(communities):
            community_to_entities[idx] = list(community_nodes)
            for node in community_nodes:
                entity_to_community[node] = idx

        result = []
        for triplet in extracted_data:
            # find the community for the subject and object
            subject_community = entity_to_community.get(triplet["subject"])
            # Create another copy to add community id
            new_triplet = triplet.copy()
            new_triplet["community_id"] = subject_community
            result.append(new_triplet)
        logger.info(
            f"[graph_service] Created community groups for {len(result)} triplets."
        )
        # Pass the commmunity to entities mapping to the llm to summarize the community and generate a description for each community
        community_descriptions = self.summarize_communities(G, community_to_entities)
        return result, community_descriptions

    def summarize_communities(
        self, G: nx.Graph, community_to_entities: Dict[int, List[str]]
    ) -> Dict[int, str]:
        summaries = {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert analyst. Analyze the following cluster of entities and relationships
            from a legal/regulatory knowledge graph. Write a concise executive summary (2-3 sentences) describing
            what this cluster or topic is about.""",
                ),
                ("human", "Community Nodes & Edges:\n{community_data}"),
            ]
        )

        chain = prompt | self.base_llm

        for comm_id, nodes in community_to_entities.items():
            # Extract subgraph for this specific community
            subgraph = G.subgraph(nodes)

            # Format community relationships into text for the LLM
            edge_list = []
            for u, v, data in subgraph.edges(data=True):
                rel = data.get("relation", "RELATED_TO")
                edge_list.append(f"- {u} {rel} {v}")

            community_text = "\n".join(edge_list)
            if not community_text:
                community_text = f"Entities: {', '.join(nodes)}"

            # Ask LLM to generate community summary
            try:
                response = chain.invoke({"community_data": community_text})
                summaries[comm_id] = response.content
            except Exception as e:
                summaries[comm_id] = f"Summary unavailable: {str(e)}"

        return summaries

    def store_in_neo4j(self, pipeline_output: Dict[str, Any]):
        """
        Stores community summaries, entity nodes, relationships, and community links in Neo4j.
        """
        logger.info(
            f"[graph_service] Storing graph data in Neo4j. Triplets count: {len(pipeline_output.get('triplets', []))}, Communities count: {len(pipeline_output.get('community_summaries', {}))}"
        )
        triplets = pipeline_output["triplets"]
        community_summaries = pipeline_output["community_summaries"]

        if not triplets and not community_summaries:
            logger.info("[graph_service] No data to store.")
            return

        logger.info("Storing Community nodes in Neo4j...")
        community_data = [
            {"id": cid, "summary": summary}
            for cid, summary in community_summaries.items()
        ]

        community_query = """
        UNWIND $communities AS c
        MERGE (com:Community {id: c.id})
        SET com.summary = c.summary
        """
        try:
            self.graph.query(community_query, {"communities": community_data})
        except Exception as e:
            logger.error(
                f"[graph_service] Error storing community data in Neo4j: {str(e)}"
            )
            return

        logger.info("Storing Entities and Relationships in Neo4j...")

        # Group triplets by relationship type to construct valid Cypher queries
        grouped_by_rel = defaultdict(list)
        for t in triplets:
            grouped_by_rel[t["relation"]].append(t)

        for rel_type, rel_triplets in grouped_by_rel.items():
            # Dynamically set the relationship label in Cypher
            entity_rel_query = f"""
            UNWIND $triplets AS t

            // 1. Merge Subject Node
            MERGE (s:Entity {{name: t.subject}})
            ON CREATE SET s.type = t.subject_type

            // 2. Merge Object Node
            MERGE (o:Entity {{name: t.object}})
            ON CREATE SET o.type = t.object_type

            // 3. Link Subject to its Community
            WITH s, o, t
            MATCH (c:Community {{id: t.community_id}})
            MERGE (s)-[:IN_COMMUNITY]->(c)

            // 4. Create/Merge Relationship between Subject and Object
            MERGE (s)-[r:{rel_type}]->(o)
            ON CREATE SET r.chunk_id = t.chunk_id
            """
            try:
                self.graph.query(entity_rel_query, {"triplets": rel_triplets})
            except Exception as e:
                logger.error(
                    f"[graph_service] Error storing triplets with relationship '{rel_type}' in Neo4j: {str(e)}"
                )
                continue  # Continue with the next relationship type

        logger.info("Successfully stored all Graph RAG data in Neo4j!")

    def index_graph_pipeline(self, chunks: List[Dict[str, Any]]):
        """
        1. Extract entities and relationships from the provided chunks using an LLM.
        2. Remove dubplicates using vector_similarity
        3. Create community grouping of the entities and relationships using graph algorithms.
        4. Store the processed data in the graph database.
        """

        # 1. Extract entities and relationships from the provided chunks using an LLM
        # Send chunk in batches
        all_results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_chunk = {
                executor.submit(self.extract_entities_and_relationships, chunk)
                for chunk in chunks
            }
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    chunk_results = future.result()
                    all_results.extend(chunk_results)
                except Exception as e:
                    logger.error(
                        f"[graph_service] Error processing chunk with chunk {chunk.get('id', 'unknown')}: {str(e)}",
                        exc_info=True,
                    )

        # 2. Remove duplicates using vector_similarity
        all_results = self.remove_duplicates(all_results)
        # 3. Create community grouping of the entities and relationships using graph algorithms.
        community_results, community_descriptions = self.create_community_group(
            all_results
        )
        # 4. Store the processed data in the graph database.
        pipeline_output = {
            "triplets": community_results,
            "community_summaries": community_descriptions,
        }
        self.store_in_neo4j(pipeline_output)
        return pipeline_output

    def local_graph_search(
        self, entities: List[str], vector_service: VectorService
    ) -> List[Dict[str, Any]]:
        """
        1. Traverses Neo4j for 1-to-2 hop relationships & gathers chunk_ids.
        2. Queries Weaviate by chunk_ids to fetch metadata and raw text.
        3. Combines graph structures with actual passage text for the AI Agent.
        """
        if not entities:
            return "No query provided for local graph search."

        cypher_query = """
        UNWIND $entities AS input_entity
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower(input_entity)

        MATCH path = (e)-[*1..2]-(neighbor:Entity)
        UNWIND relationships(path) AS rel

        RETURN DISTINCT
            startNode(rel).name AS source,
            type(rel) AS relation,
            endNode(rel).name AS target,
            coalesce(rel.chunk_ids, [rel.chunk_id]) AS chunk_ids
        LIMIT 30
        """

        try:
            results = self.graph.query(cypher_query, {"entities": entities})
            if not results:
                return {
                    "context": "No graph context found.",
                    "sources": [],
                    "graph_context": [],
                }

            graph_context = []
            all_chunk_ids = set()

            for r in results:
                source = r["source"]
                relation = r["relation"]
                target = r["target"]
                chunk_ids = r.get("chunk_ids") or []

                all_chunk_ids.update(chunk_ids)

                # Build structured graph context item
                graph_context.append(
                    {
                        "source_node": source,
                        "relationship": relation,
                        "target_node": target,
                        "graph_path": f"({source})-[:{relation}]->({target})",
                    }
                )

            # Query Weaviate using collected chunk IDs
            weaviate_chunks = vector_service.get_chunks_by_ids(list(all_chunk_ids))

            sources = []
            text_passages = []

            for chunk_id, data in weaviate_chunks.items():
                sources.append(
                    {
                        "document_id": data.get("document_id", "unknown"),
                        "document": data.get("filename", "document.pdf"),
                        "title": data.get("title", "Untitled Document"),
                        "page": data.get("page_number", 1),
                        "snippet": data.get("text", "")[:200] + "...",
                    }
                )
                text_passages.append(f"Excerpt: \"{data.get('text', '')}\"")

            # Combine into LLM context text
            formatted_facts = [g["graph_path"] for g in graph_context]
            context_text = "### GRAPH FACTS\n" + "\n".join(formatted_facts)
            context_text += "\n\n### RETRIEVED EXCERPTS\n" + "\n\n".join(text_passages)

            return {
                "context": context_text,
                "sources": sources,
                "graph_context": graph_context,
            }

        except Exception as e:
            logger.error(f"Error in local_graph_search: {str(e)}")
            # return f"Error executing local graph search: {str(e)}"
            raise Exception(f"Error executing local graph search: {str(e)}")

    def global_graph_search(self, query: str) -> str:
        """
        Global search uses the pre-computed Community Summaries to answer
        broad, dataset-wide questions by synthesizing overarching themes.
        """
        logger.info(f"[graph_service] Running global graph search for query: {query}")

        # 1. Fetch all community summaries from Neo4j
        cypher_query = """
        MATCH (c:Community)
        WHERE c.summary IS NOT NULL
        RETURN c.id AS community_id, c.summary AS summary
        """

        try:
            records = self.graph.query(cypher_query)
        except Exception as e:
            logger.error(f"[graph_service] Error fetching communities: {str(e)}")
            raise Exception(f"Error fetching communities: {str(e)}")

        if not records:
            logger.warning("[graph_service] No community summaries found in the graph.")
            raise Exception(
                "No community summaries found in the graph to answer the query."
            )

        # 2. Combine all community summaries into a single context block
        context_parts = []
        graph_context = []
        for record in records:
            comm_id = str(record.get("community_id"))
            summary = record.get("summary", "")
            graph_context.append(
                {
                    "source_node": f"Community_{comm_id}",
                    "relationship": "SUMMARIZES_CLUSTER",
                    "target_node": f"Topic Cluster {comm_id}",
                    "graph_path": f"(Community_{comm_id})-[SUMMARIZES_CLUSTER]->({summary[:80]}...)",
                }
            )
            context_parts.append(
                f"--- Community {record['community_id']} ---\n{record['summary']}"
            )

        context_text = "\n\n".join(context_parts)

        return {
            "context_text": context_text,
            "graph_context": graph_context,
            "sources": [],
        }


graph_service = GraphService()
