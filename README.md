# Attijary GraphRAG

<p align="center">
  <strong>Enterprise regulatory monitoring assistant powered by hybrid GraphRAG search</strong>
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#api-reference">API Reference</a> ·
  <a href="#infrastructure--deployment">Infrastructure</a> ·
  <a href="#local-development">Local Development</a>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white" alt="Flask"></a>
  <a href="https://azure.microsoft.com/"><img src="https://img.shields.io/badge/Microsoft%20Azure-0078D4?logo=microsoftazure&logoColor=white" alt="Azure"></a>
  <a href="https://www.terraform.io/"><img src="https://img.shields.io/badge/Terraform-844FBA?logo=terraform&logoColor=white" alt="Terraform"></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/features/actions"><img src="https://img.shields.io/badge/GitHub%20Actions-2088FF?logo=githubactions&logoColor=white" alt="GitHub Actions"></a>
  <a href="https://neo4j.com/"><img src="https://img.shields.io/badge/Neo4j-4581C3?logo=neo4j&logoColor=white" alt="Neo4j"></a>
  <a href="https://weaviate.io/"><img src="https://img.shields.io/badge/Weaviate-00A98F?logo=weaviate&logoColor=white" alt="Weaviate"></a>
</p>

## Overview

Attijary GraphRAG is a full-stack regulatory monitoring platform that enables authorized users to ingest regulatory documents, build searchable knowledge representations, and ask grounded questions over enterprise content.

The project demonstrates production-oriented software engineering across application development, AI orchestration, asynchronous processing, cloud infrastructure, observability, and DevSecOps:

- **Angular frontend** for authentication, document administration, query submission, conversation history, and source-aware answer rendering.
- **Python/Flask API** organized around versioned blueprints and service boundaries.
- **LangChain and GraphRAG** orchestration combining vector, keyword, and graph retrieval.
- **Celery and Redis** for asynchronous document indexing, deletion, and audit workloads.
- **PostgreSQL** for users, documents, chats, conversations, and audit records.
- **Weaviate** for semantic and hybrid retrieval.
- **Neo4j** for entities, relationships, and graph traversal.
- **Azure Blob Storage and Key Vault** for durable document storage and secret management.
- **Terraform and GitHub Actions** for repeatable infrastructure delivery and security automation.

## Table of Contents

- [Application Showcase](#-application-showcase)
- [Core Capabilities](#core-capabilities)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Enterprise Security and Reliability](#enterprise-security-and-reliability)
- [Infrastructure & Deployment](#infrastructure--deployment)
- [Local Development](#local-development)
- [Repository Structure](#repository-structure)
- [Engineering Notes](#engineering-notes)

## 📸 Application Showcase



<p align="center"><img width="1917" height="867" alt="Screenshot 2026-10-17 101720" src="https://github.com/user-attachments/assets/a4f15ef5-df60-400a-8330-de79b4b11e4d" /></p> 
<p align="center"><em>Grounded conversational query experience with retrieved sources.</em></p>

<p align="center"><img width="1917" height="867" alt="Screenshot 2026-10-17 101808" src="https://github.com/user-attachments/assets/8022f1f7-b0e6-4566-96e6-caefc0165f15" /></p>
<p align="center"><em>Document upload, metadata capture, and indexing workflow.</em></p>

<p align="center"><<img width="1917" height="861" alt="Screenshot 2026-10-17 101911" src="https://github.com/user-attachments/assets/bbc4d1d3-827e-4ff0-9368-fb8604afee5f" /></p>
<p align="center"><em>Structured administrative audit-log view.</em></p>

<p align="center"><img width="1917" height="882" alt="Screenshot 2026-10-17 102008" src="https://github.com/user-attachments/assets/639f55f0-338d-403a-9ba7-ce8a7ab9f9d0" /></p>
<p align="center"><em>Document graph relationship.</em></p>

## Core Capabilities

### Hybrid GraphRAG query experience

The query pipeline classifies and routes user questions before selecting the most appropriate retrieval strategy:

1. Authenticate the request and load conversation context.
2. Refactor and classify the query with a fast routing model.
3. Use hybrid vector/keyword search for document-grounded questions.
4. Fall back to an agentic graph workflow for entity and relationship-heavy questions.
5. Synthesize an answer with the language model.
6. Persist the response and its retrieval metadata for traceability.

### Document ingestion pipeline

Documents are uploaded directly to Azure Blob Storage using a generated SAS URL. Indexing is deliberately asynchronous so the API remains responsive while workers extract text, create chunks, generate embeddings, write Weaviate vectors, extract graph entities, and persist Neo4j relationships.

### Administrative controls

Document administration and audit-log access are protected with authentication and role-based authorization. Administrators can manage the document lifecycle and review audit activity, while document reads are scoped to the requesting user unless the caller has the administrator role.

## Technology Stack

| Layer | Technologies |
| --- | --- |
| Frontend | Angular 19, TypeScript, SCSS, Nginx |
| API | Python, Flask, Gunicorn, Flask-CORS, SQLAlchemy, Alembic |
| AI/RAG | LangChain, GraphRAG patterns, Google Gemini, hybrid retrieval |
| Data | Supabase PostgreSQL, Weaviate Cloud, Neo4j Cloud |
| Background processing | Celery, Redis |
| Identity and secrets | Clerk authentication, Azure Key Vault, Azure managed identity/OIDC |
| Storage | Azure Blob Storage with SAS-based uploads |
| Platform | Docker, Docker Compose, Azure VM |
| Infrastructure | Terraform with modular production environment configuration |
| Delivery and security | GitHub Actions, CodeQL, Trivy, dependency review |
| Performance validation | Locust and k6 load-testing assets |

## Architecture

### System Context

```mermaid
flowchart LR
    user([User])
    identity([Identity Provider])
    model([Language Model Service])
    file_store([Document Storage])
    record_store([Operational Data Store])
    vector_store([Semantic Search Service])
    graph_store([Knowledge Graph Service])

    system["GraphRAG System"]

    user -->|Submits questions and documents| system
    system -->|Returns answers, search results, and processing status| user

    system <-->|Authenticates users and validates sessions| identity
    system <-->|Sends prompts and receives generated responses| model
    system <-->|Stores and retrieves document files| file_store
    system <-->|Stores users, conversations, documents, and audit records| record_store
    system <-->|Creates representations and retrieves relevant content| vector_store
    system <-->|Builds and queries connected knowledge| graph_store

    classDef actor fill:#fff4cc,stroke:#9a6700,color:#24292f,stroke-width:2px
    classDef system fill:#000000,stroke:#000000,color:#ffffff,stroke-width:3px
    classDef dependency fill:#ffffff,stroke:#5b6470,color:#24292f,stroke-width:1px

    class user actor
    class system system
    class identity,model,file_store,record_store,vector_store,graph_store dependency
```

### Deployment Topology

<img width="1698" height="751" alt="Screenshot 2026-10-15 115356" src="https://github.com/user-attachments/assets/3e1988fe-ad26-4a5e-865a-a4dcb8ad4b71" />



### RAG Query Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Angular as Angular Frontend
    participant API as Flask API
    participant Clerk as Clerk Authentication
    participant PostgreSQL as PostgreSQL DB
    participant Router as Gemini Quick Model (Router)
    participant Agent as LangChain Agent Executor
    participant Weaviate as Weaviate (Vector)
    participant Neo4j as Neo4j (Graph)
    participant Gemini as Gemini LLM

    User->>Angular: Submit query
    Angular->>API: POST /api/v1/agent/query
    API->>Clerk: Validate Auth Token
    Clerk-->>API: User Context
    API->>PostgreSQL: Save User Message & Load History
    PostgreSQL-->>API: History context
    API->>Router: Refactor query & classify intent
    Router-->>API: routed_method, refactored_query

    alt routed_method == hybrid_search_tool
        API->>Weaviate: Hybrid search (vector + keyword)
        Weaviate-->>API: Text chunks & metadata
        API->>Gemini: Quick answer synthesis
        Gemini-->>API: Generated answer
    else routed_method == unrelated_or_conversational
        API->>Gemini: Conversational LLM call
        Gemini-->>API: Conversational answer
    else Agent fallback / graph
        API->>Agent: Invoke Agent Executor
        opt Tool Execution Loop
            Agent->>Neo4j: Query local/global graph
            Neo4j-->>Agent: Entities & relationships
            Agent->>Weaviate: Run hybrid vector search
            Weaviate-->>Agent: Text chunks
            Agent->>Gemini: Tool output synthesis
            Gemini-->>Agent: Final Agent Output
        end
        Agent-->>API: Agent response & intermediate artifacts
    end

    API->>PostgreSQL: Persist Assistant response & rag_source
    PostgreSQL-->>API: Commit successful
    API-->>Angular: JSON Response (content, sources, rag_source)
    Angular-->>User: Render response
```

### Document Ingestion Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant Angular as Angular Frontend
    participant API as Flask API
    participant PostgreSQL as PostgreSQL
    participant Blob as Azure Blob Storage
    participant Redis as Redis Broker
    participant Worker as Celery Indexing Worker
    participant Extractor as Text Extractor
    participant Chunker as Chunking Service
    participant Embeddings as Gemini Embedding Model
    participant Weaviate as Weaviate Vector Database
    participant Graph as Graph Extraction Service
    participant Neo4j as Neo4j Graph Database

    Admin->>Angular: Start document upload
    Angular->>API: POST /api/v1/documents/upload-url
    API->>PostgreSQL: Create document with PENDING_UPLOAD status
    PostgreSQL-->>API: Document record
    API->>Blob: Generate upload SAS URL
    Blob-->>API: SAS upload URL
    API-->>Angular: Return document metadata and upload URL
    Angular->>Blob: Upload document file
    Blob-->>Angular: Upload completed

    Admin->>Angular: Start document indexing
    Angular->>API: POST /api/v1/documents/{id}/index
    API->>PostgreSQL: Set status to PROCESSING
    API->>Redis: Enqueue indexing task
    Redis-->>API: Task identifier
    API-->>Angular: Return 202 and task identifier

    Redis->>Worker: Deliver indexing task
    Worker->>Blob: Download document
    Blob-->>Worker: Document file
    Worker->>Extractor: Extract text and pages
    Extractor-->>Worker: Page text
    Worker->>Chunker: Split text into chunks
    Chunker-->>Worker: Document chunks
    Worker->>Embeddings: Generate embeddings in batches
    Embeddings-->>Worker: Chunk vectors
    Worker->>Weaviate: Store vectors and chunk metadata
    Weaviate-->>Worker: Vector index confirmed
    Worker->>Graph: Extract entities and relationships
    Graph-->>Worker: Graph nodes and edges
    Worker->>Neo4j: Store graph data
    Neo4j-->>Worker: Graph index confirmed
    Worker->>PostgreSQL: Set status to ACTIVE_COMPLETED
    PostgreSQL-->>Worker: Status committed
```

### Data Model

```mermaid
erDiagram
    USER ||--o{ DOCUMENT : uploads
    USER ||--o{ CHAT : owns
    USER ||--o{ AUDIT_LOG : creates
    CHAT ||--o{ CONVERSATION : contains
    DOCUMENT ||--o{ DOCUMENT_CHUNK : is_indexed_as
    GRAPH_ENTITY ||--o{ GRAPH_RELATIONSHIP : source
    GRAPH_ENTITY ||--o{ GRAPH_RELATIONSHIP : target

    USER {
        uuid user_id PK
        string firstname
        string lastname
        string email UK
        string role
        string clerk_id UK
        datetime created_at
        datetime updated_at
    }

    DOCUMENT {
        uuid document_id PK
        uuid uploaded_by_user_id FK
        string title
        string number
        datetime date
        string category
        string file_path
        string file_extension
        string status
        string origin
        string source_url
    }

    CHAT {
        uuid chat_id PK
        uuid user_id FK
        string title
        datetime created_at
    }

    CONVERSATION {
        uuid conversation_id PK
        uuid chat_id FK
        string role
        text content
        datetime created_at
        jsonb rag_source
    }

    AUDIT_LOG {
        uuid id PK
        uuid actor_id FK
        string action
        uuid target_id
        string target_resource
        string ip_address
        string details
        datetime created_at
    }

    DOCUMENT_CHUNK {
        string chunk_id PK
        uuid document_id FK
        int page_number
        text content
        vector embedding
    }

    GRAPH_ENTITY {
        string entity_id PK
        uuid document_id FK
        string entity_type
        string name
    }

    GRAPH_RELATIONSHIP {
        string relationship_id PK
        string source_entity_id FK
        string target_entity_id FK
        string relationship_type
    }
```

### Asynchronous Task Architecture

```mermaid
flowchart LR
    api[Flask API]
    redis[(Redis Broker)]

    subgraph queues[Celery Queues]
        indexing[Document Indexing Queue]
        deletion[Document Deletion Queue]
        audit[Audit Log Queue]
    end

    subgraph workers[Celery Workers]
        index_worker[Indexing Worker]
        delete_worker[Deletion Worker]
        audit_worker[Audit Worker]
    end

    subgraph services[External Services]
        storage[Azure Blob Storage]
        vector[Weaviate Cloud]
        graph_db[Neo4j Cloud]
        database[(Supabase PostgreSQL)]
        llm[Google Gemini API]
    end

    api -->|Enqueue task| redis
    redis --> indexing
    redis --> deletion
    redis --> audit
    indexing --> index_worker
    deletion --> delete_worker
    audit --> audit_worker

    index_worker --> storage
    index_worker --> vector
    index_worker --> graph_db
    index_worker --> database
    index_worker --> llm
    delete_worker --> storage
    delete_worker --> vector
    delete_worker --> graph_db
    delete_worker --> database
    audit_worker --> database

    subgraph lifecycle[Task Lifecycle]
        queued[QUEUED] --> running[RUNNING]
        running --> completed[COMPLETED]
        running --> failed[FAILED]
        running --> cancelled[CANCELLED]
    end

    redis -.->|Initial state| queued
    index_worker -.->|Updates state| running
    index_worker -.->|Success| completed
    index_worker -.->|Error or retry limit| failed
    index_worker -.->|Cancellation requested| cancelled
```

Source diagram files are maintained in [`docs/architecture/`](docs/architecture/), alongside audit-log documentation.

## API Reference

All protected endpoints expect a valid Clerk bearer token in the `Authorization` header. Responses use a consistent JSON envelope where applicable:

```json
{
  "status": "success",
  "data": {},
  "meta": {}
}
```

### Health and readiness

| Method | Path | Auth | Description | Response |
| --- | --- | --- | --- | --- |
| `GET` | `/health` | Public | Lightweight liveness check. | `200` — `{ "status": "healthy", "environment": "..." }` |
| `GET` | `/healthz/ready` | Public | Readiness check for PostgreSQL, Weaviate, and Neo4j connectivity. | `200` when ready; `503` with `{ "status": "unhealthy", "error": "Service temporarily unavailable" }` otherwise |

### Authentication and RBAC

| Method | Path | Auth | Description | Response |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/sync` | Clerk bearer token | Synchronizes the authenticated Clerk user with the application database. | `200` — serialized user profile |
| `GET` | `/api/v1/protected-route-test` | Authenticated | Authenticated-access smoke test. | `200` — user ID confirmation |
| `GET` | `/api/v1/admin-route-test` | Admin | Administrator-access smoke test. | `200` — admin user ID confirmation |

### Document ingestion and lifecycle

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/documents/` | Admin | Paginated document list. Supports `page`, `limit`, and optional `status` query parameters. |
| `POST` | `/api/v1/documents/upload-url` | Admin | Creates a `PENDING_UPLOAD` record and returns an Azure Blob SAS upload URL. |
| `POST` | `/api/v1/documents/{document_id}/index` | Admin | Enqueues asynchronous extraction, chunking, embedding, vector indexing, and graph indexing. |
| `GET` | `/api/v1/documents/{document_id}` | Authenticated | Returns a document when the caller owns it or has the admin role. |
| `DELETE` | `/api/v1/documents/{document_id}` | Admin | Marks a document for deletion and enqueues cascading cleanup. |

**Create upload URL request:**

```json
{
  "filename": "regulation-2026.pdf",
  "title": "Regulatory Notice 2026",
  "number": "RN-2026-001",
  "category": "Risk"
}
```

**Create upload URL response (`201`):**

```json
{
  "status": "success",
  "data": {
    "document": {
      "document_id": "uuid",
      "title": "Regulatory Notice 2026",
      "status": "PENDING_UPLOAD"
    },
    "upload_url": "https://storage.example/...sas-token..."
  }
}
```

**Index response (`202`):**

```json
{
  "status": "success",
  "data": {
    "document_id": "uuid",
    "task_id": "celery-task-id",
    "message": "Indexing pipeline enqueued"
  }
}
```

### GraphRAG queries and conversations

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/agent/query` | Authenticated | Executes the routed GraphRAG/agent flow and persists the conversation. |
| `GET` | `/api/v1/agent/chats` | Authenticated | Lists chat sessions belonging to the authenticated user. |
| `GET` | `/api/v1/agent/chats/{chat_id}/messages` | Authenticated | Returns the messages for a chat session. |

**Query request:**

```json
{
  "query": "What obligations apply to liquidity risk reporting?",
  "chat_id": "optional-chat-uuid"
}
```

**Query response shape:**

```json
{
  "content": "Grounded assistant response...",
  "sources": [],
  "rag_source": {},
  "chat_id": "chat-uuid"
}
```

The exact source and intermediate-artifact fields are service-defined and are persisted with the assistant response to support traceability and future conversation context.

### Audit logs

| Method | Path | Role | Query parameters | Response |
| --- | --- | --- | --- | --- |
| `GET` | `/api/v1/audits/logs` | Admin | `page`, `limit` | `200` — `{ "status": "success", "data": [...], "meta": {...} }` |

Audit entries include actor, action, target resource, target ID, source IP address, details, and creation timestamp. HTTP request logging is emitted as structured JSON with method, path, status, latency, IP, user agent, and authenticated user context where available.

## Enterprise Security and Reliability

- **Authentication:** Clerk-issued bearer tokens are validated by backend middleware.
- **RBAC:** Admin-only routes use a dedicated `admin_required` guard; regular document access is ownership-scoped.
- **Secret management:** Production/staging configurations load secrets from Azure Key Vault; local development uses environment files.
- **Least-privilege CI authentication:** Azure deployments use GitHub Actions OIDC with `id-token: write`, avoiding long-lived cloud credentials in workflows.
- **Structured auditability:** Administrative actions and HTTP requests are represented in structured logs and persisted audit records.
- **Asynchronous isolation:** Long-running ingestion and deletion operations are moved to Celery workers, returning `202 Accepted` and task identifiers to clients.
- **Dependency health:** Readiness checks validate PostgreSQL, Weaviate, and Neo4j connections before traffic is considered healthy.
- **Security scanning:** CodeQL, dependency review, secret scanning, and Trivy infrastructure configuration scans are integrated into GitHub Actions.
- **Operational resilience:** Database connection pooling, pre-ping, recycling, task lifecycle states, retries, and container health checks support production operations.

## Infrastructure & Deployment

Production Terraform is organized under [`infrastructure/terraform/environments/prod`](infrastructure/terraform/environments/prod) and composes reusable modules for Azure storage and the application virtual machine.

### Terraform workflow

```bash
cd infrastructure/terraform/environments/prod
terraform fmt -recursive
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
```

The AzureRM backend stores Terraform state in Azure Blob Storage with Azure AD authentication. The provider is configured for Azure OIDC and Azure AD-backed storage access.

### Azure identity and environment setup

The CI workflow authenticates to Azure with GitHub Actions OIDC using:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `ARM_USE_OIDC=true`

Runtime workloads use managed identity-oriented configuration for Azure resources and Key Vault access. Keep environment-specific values and private keys in GitHub environment secrets or Azure Key Vault rather than committing them to the repository.

### CI/CD security gates

GitHub Actions workflows cover frontend/backend CI, Docker image builds, infrastructure validation, and production delivery. The infrastructure pipeline:

1. Formats and validates Terraform.
2. Authenticates to Azure through OIDC.
3. Runs Trivy configuration scanning.
4. Creates and uploads a Terraform plan artifact.
5. Applies the approved plan only on pushes to `main` through the protected `production` environment.

Reusable security workflows provide CodeQL analysis, dependency review, and secret scanning. CodeQL is configured for Python analysis and dependency review can fail on high-severity vulnerabilities or unapproved licenses.

## Local Development

### Prerequisites

- Docker Desktop with Docker Compose
- Git
- A configured `.env` file for `backend/`
- A configured `.env` file for `frontend/`
- Access credentials for external services when running the full integration path: Clerk, PostgreSQL/Supabase, Redis, Weaviate, Neo4j, Azure Blob Storage, and Gemini

### Start the application

```bash
git clone https://github.com/chedy322/Attijary-graph-rag.git
cd Attijary-graph-rag

# Create local environment files from your team-approved templates.
# Do not commit secrets.
cp backend/.env.example backend/.env 2>/dev/null || true
cp frontend/.env.example frontend/.env 2>/dev/null || true

# Build and start the frontend, Flask API, and Celery worker.
docker compose up --build
```

The Compose configuration exposes:

- Frontend: `http://localhost:4200`
- Backend API: `http://localhost:3000`
- Backend container port: `5000`
- Liveness endpoint: `http://localhost:3000/health`
- Readiness endpoint: `http://localhost:3000/healthz/ready`

The repository currently expects Redis and several managed services to be supplied through environment configuration. If you prefer to run the backend directly, install the Python dependencies from `backend/requirements.txt` and start the Flask application from the backend source environment.

### Run the Celery worker directly

```bash
cd backend
celery -A celery_worker.celery_app worker --loglevel=info --pool=threads
```

### Frontend-only development

```bash
cd frontend
npm install
ng serve
```

Then open `http://localhost:4200/`.

## Repository Structure

```text
.
├── backend/                         # Flask API, services, models, tasks, and Dockerfile
│   └── src/
├── frontend/                        # Angular application and static hosting configuration
├── infrastructure/
│   └── terraform/
│       ├── environments/prod/       # Production composition and Azure backend config
│       └── modules/                 # Reusable Azure infrastructure modules
├── docs/
│   └── architecture/                # Mermaid architecture and audit-log documentation
├── .github/workflows/               # CI, CD, Terraform, CodeQL, Trivy, and scanning workflows
├── docker-compose.yaml               # Local multi-container orchestration
└── vm-docker-compose.yml             # VM-oriented deployment composition
```

## Engineering Notes

This repository is intentionally structured to demonstrate end-to-end ownership:

- Clear separation between transport-layer blueprints, domain services, persistence models, and asynchronous tasks.
- Versioned API contracts under `/api/v1`.
- Hybrid retrieval that combines semantic similarity, keyword matching, and connected graph context.
- Explicit lifecycle states for document processing and task execution.
- Cloud-native delivery with immutable containers, infrastructure as code, OIDC authentication, and security scanning.
- Architecture artifacts that make system boundaries, data flows, deployment topology, and operational behavior reviewable by engineering teams.
