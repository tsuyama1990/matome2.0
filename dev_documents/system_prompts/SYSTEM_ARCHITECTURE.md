# System Architecture Document

## 1. Summary
matome (meaning "summary" in Japanese) is a revolutionary knowledge workspace designed to transform the painful process of reading and summarising large documents into an engaging, interactive game of intellectual discovery. By integrating cognitive psychology principles—such as the SQ3R method, cognitive load theory, the Feynman technique, and the spacing effect—with advanced generative AI capabilities including Multi-Dimensional Semantic KJ (MD-SKJ) and RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval), matome acts as a frictionless active learning platform. The system does not merely shorten text; it builds a robust knowledge network in the user's mind, supporting everything from initial reading to the generation of highly complex output documents like Product Requirements Documents (PRDs) and sequence diagrams.

## 2. System Design Objectives
The primary objective of the matome platform is to completely eradicate the cognitive overload and friction typically associated with processing vast amounts of information. To achieve this, the system design is governed by several critical constraints, goals, and success criteria.

Firstly, the platform must guarantee an ultra-low latency response to maintain a state of psychological "flow" for the user. When users interact with the system—for example, by answering an AI-generated question to unlock a node—the system must provide visual feedback within milliseconds and start streaming AI-generated text within 1.0 second (Time To First Token). This demands a highly optimised backend architecture, leveraging asynchronous I/O, streaming API endpoints, and aggressive prompt caching to prevent blocking the main execution thread. The frontend must be equally performant, capable of rendering thousands of interactive nodes on an infinite canvas at a steady 60 frames per second using technologies like WebGL and canvas virtualization, ensuring no UI stuttering even during complex physical animations.

Secondly, the system must enforce strict separation of concerns to avoid the creation of monolithic "God Classes." The architecture must isolate the AI model interaction logic from the core domain logic and the HTTP transport layer. By doing so, the system remains highly modular and adaptable, allowing engineers to swap out underlying Large Language Models (LLMs) or vector databases without refactoring the entire application. We will use the Dependency Injection pattern extensively, mapping external clients (such as OpenRouter API clients) as injected resources whose lifecycles are explicitly managed. This ensures that the system is easily testable through mocked dependencies, preventing fragile tests that rely on network calls.

Thirdly, the system must guarantee absolute data privacy and security, especially to meet enterprise standards. The system design must accommodate a "Zero-Data Retention" policy for document processing, meaning user documents and proprietary data are never used to train external AI models. We will implement robust API key management supporting a Bring Your Own Key (BYOK) model, where user credentials are encrypted via AES-256-GCM. Additionally, the architecture must support a fallback mechanism to local or private VPC-hosted LLMs for highly sensitive environments, strictly decoupling the AI provider interface from the business logic so that routing decisions can be made dynamically based on user configuration and data classification.

Finally, the design must remain resilient and cost-effective. We will implement intelligent model routing via OpenRouter, automatically directing simple tasks (like basic chunking or entity extraction) to faster, cheaper models, while reserving heavy reasoning tasks (like multi-dimensional KJ analysis or Web-Grounding) for advanced models. The system must also include automatic fallback mechanisms to alternative models in the event of API timeouts. This resilience extends to the orchestration of complex AI workflows using LangGraph, treating multi-step document processing as a state machine. This allows the system to recover from intermittent failures without restarting the entire pipeline, ultimately resulting in a stable, scalable, and highly available platform capable of handling massive document ingestion concurrently without memory exhaustion (OOM), ensuring file streaming and batch processing are utilised strictly.

## 3. System Architecture
The architecture of matome is designed to be highly modular, scalable, and resilient, following modern software design patterns. The system is divided into three primary tiers: the Client Tier (Frontend), the Application Tier (Backend), and the Data & AI Tier.

The Client Tier will be built as a Single Page Application (SPA) using React and React Flow to manage the complex, highly interactive node-based infinite canvas. The frontend is responsible for rendering the Semantic Zoom UI, handling user interactions (such as voice input via the Web Speech API and pinch-to-zoom gestures), and managing local state to ensure 60fps animations. It communicates with the backend exclusively via RESTful APIs and WebSockets (for streaming AI responses and real-time layout updates).

The Application Tier is built on Python 3.12+ using FastAPI, providing a high-performance, asynchronous foundation. To guarantee strict boundary management and separation of concerns, the backend strictly adheres to an Onion/Clean Architecture pattern.
- **Presentation Layer:** Contains FastAPI routers, request validation using Pydantic V2 models, and response serialization. It handles HTTP concerns only.
- **Service Layer (Use Cases):** Contains the core business logic, orchestrating workflows using LangGraph. It knows nothing about HTTP or specific database implementations.
- **Domain Layer:** Contains pure Pydantic models defining the core entities (e.g., Document, Chunk, Node, Concept) and abstract interfaces (Ports) for external dependencies.
- **Infrastructure Layer:** Contains concrete implementations of interfaces, such as vector database adapters (Pinecone/Qdrant), LLM clients (via OpenRouter), and local file system adapters.

Explicit Rules on Boundary Management:
1. Dependencies must point inwards towards the Domain Layer. The Domain Layer must not import from the Infrastructure or Presentation layers.
2. All external interactions (LLMs, Vector DBs, external APIs) must be hidden behind abstract interfaces defined in the Domain Layer.
3. Dependency Injection must be used to provide concrete implementations to the Service Layer at runtime, enabling complete isolation for unit testing.
4. Large file processing must never load the entire payload into memory. Generator-based streaming and `aiofiles` must be used strictly to prevent Path Traversal vulnerabilities and OOM errors.

The Data & AI Tier consists of a Vector Database for semantic search and retrieval (HNSW indexing), a relational database (SQLite/PostgreSQL) for user metadata and configuration, and OpenRouter as the central gateway to various LLMs. LangGraph is utilized within the Service layer to manage the stateful workflow of document processing, such as the RAPTOR chunking pipeline and the Pivot KJ analysis, ensuring that long-running tasks can be retried, paused, or resumed reliably.

```mermaid
graph TD
    subgraph Client Tier
        UI[React + React Flow UI]
        Audio[Web Speech API]
    end

    subgraph Presentation Layer
        API[FastAPI Routers]
        WS[WebSocket Endpoints]
    end

    subgraph Service Layer
        Orchestrator[LangGraph Orchestrator]
        Chunking[Semantic Chunking Service]
        RAPTOR[RAPTOR Tree Builder]
        KJ[Pivot KJ Engine]
        DI[Dependency Injector]
    end

    subgraph Domain Layer
        Models[Pydantic Domain Models]
        Interfaces[Abstract Base Classes]
    end

    subgraph Infrastructure Layer
        VDB_Adapter[Vector DB Adapter]
        LLM_Adapter[OpenRouter LLM Client]
        File_Storage[Local/Cloud File Storage]
    end

    subgraph Data & AI Tier
        VectorDB[(Qdrant / Pinecone)]
        OpenRouter((OpenRouter API))
        SQLite[(Metadata DB)]
    end

    UI --> API
    UI <--> WS
    Audio --> API

    API --> Orchestrator
    WS --> Orchestrator

    Orchestrator --> Chunking
    Orchestrator --> RAPTOR
    Orchestrator --> KJ

    Chunking --> Models
    RAPTOR --> Models
    KJ --> Models

    DI --> VDB_Adapter
    DI --> LLM_Adapter
    DI --> File_Storage

    Service Layer -.-> |Injected| Infrastructure Layer
    Infrastructure Layer -.-> Interfaces

    VDB_Adapter --> VectorDB
    LLM_Adapter --> OpenRouter
    File_Storage --> SQLite
```

## 4. Design Architecture
The codebase acts as the single source of truth and enforces strict Python typing, linting (Ruff), and complexity constraints. We will expand the existing minimal `main.py` setup into a full-fledged robust backend. The new modules will integrate seamlessly by defining clear interfaces and adhering to the existing standard.

### File Structure
```text
matome2-0/
├── pyproject.toml
├── main.py (Entry point, FastAPI app setup)
├── src/
│   ├── api/
│   │   ├── dependencies.py (FastAPI DI)
│   │   ├── routers/
│   │   │   ├── documents.py
│   │   │   ├── study.py
│   │   │   └── export.py
│   ├── core/
│   │   ├── config.py (Pydantic BaseSettings, central config)
│   │   ├── exceptions.py
│   │   └── security.py
│   ├── domain/
│   │   ├── models/
│   │   │   ├── document.py (Pydantic Core Models)
│   │   │   ├── node.py (Graph/Tree Models)
│   │   │   └── config.py (User Settings Models)
│   │   └── ports/
│   │       ├── llm.py (ILLMProvider interface)
│   │       ├── vector_store.py (IVectorStore interface)
│   │       └── storage.py (IFileStorage interface)
│   ├── services/
│   │   ├── ingestion_workflow.py (LangGraph definition)
│   │   ├── raptor_builder.py
│   │   └── kj_analyzer.py
│   └── infrastructure/
│       ├── openrouter_client.py (Implements ILLMProvider)
│       ├── qdrant_client.py (Implements IVectorStore)
│       └── local_storage.py (Implements IFileStorage)
└── tests/
    ├── conftest.py (TestConfigFactory)
    ├── unit/
    ├── integration/
    └── e2e/
```

### Core Domain Pydantic Models Structure
We adhere to Schema-First design. All domain models enforce strict validation with `model_config = ConfigDict(extra="forbid")`.

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from uuid import UUID

class BaseDomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

class DocumentChunk(BaseDomainModel):
    chunk_id: UUID
    document_id: UUID
    text: str = Field(..., description="The semantic proposition text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities and tags")
    embedding: Optional[List[float]] = None

class ConceptNode(BaseDomainModel):
    node_id: UUID
    parent_id: Optional[UUID] = None
    title: str
    summary: str = Field(..., description="High-density summary via Chain of Density")
    level: int = Field(..., ge=0)
    is_unlocked: bool = Field(default=False)
    chunk_references: List[UUID] = Field(default_factory=list)

class AnalysisAxis(BaseDomainModel):
    name: str = Field(..., description="e.g., SWOT, Timeline, Actor-State")
    dimensions: List[str] = Field(..., description="Categories within the axis")

class PivotBoard(BaseDomainModel):
    board_id: UUID
    original_document_id: UUID
    axis: AnalysisAxis
    clusters: Dict[str, List[ConceptNode]] = Field(default_factory=dict)
```

Integration Points: The `main.py` will be modified solely to mount the FastAPI application and register the Dependency Injector container. The new schema objects naturally act as the data transfer objects passed between the decoupled layers. Any future features simply introduce new routers, new use-case services, and domain models that implement the existing base classes, ensuring backwards compatibility and an evolutionary growth path without destroying core stability.

## 5. Implementation Plan
The implementation is broken down into 8 sequential cycles, strictly isolating concerns and ensuring that tests dictate the implementation (TDD).

### Cycle 01: Core Infrastructure & Domain Scaffolding
**Goal:** Establish the strict architectural baseline, configure Pydantic settings, and define the core Domain Models and Interfaces (Ports).
**Details:** We will define the `config.py` using Pydantic `BaseSettings` populated via environment variables using `Field(default_factory=os.getenv)`. We will construct the foundational domain models (e.g., `DocumentChunk`, `ConceptNode`) with strict validation. Abstract interfaces for `ILLMProvider`, `IVectorStore`, and `IFileStorage` will be defined to establish the boundary rules. No concrete external APIs will be connected yet. We will set up the Dependency Injection container to yield mock resources. This cycle proves that the architecture enforces separation of concerns and type safety before any complex logic is written.
**Deliverables:** `src/core/config.py`, `src/domain/models/`, `src/domain/ports/`, initial FastAPI app setup in `main.py`.

### Cycle 02: Infrastructure Adapters Implementation
**Goal:** Implement the concrete infrastructure classes that communicate with the outside world, adhering to the ports defined in Cycle 01.
**Details:** We will implement the `OpenRouterClient` utilizing `httpx.AsyncClient` with proper connection pooling and lifecycle management explicitly yielding and awaiting `.close()`. We will also implement a lightweight, local-first vector store adapter (e.g., utilizing an in-memory or SQLite-based HNSW index if a dedicated DB is overkill for early testing, or preparing the Qdrant API client). The local file storage adapter will be implemented utilizing `aiofiles` in binary mode to ensure memory-safe streaming of uploaded documents, preventing OOM.
**Deliverables:** `src/infrastructure/openrouter_client.py`, `src/infrastructure/vector_client.py`, `src/infrastructure/local_storage.py`.

### Cycle 03: Document Ingestion & Safe File Handling
**Goal:** Implement the REST API endpoints and service logic for uploading and securely handling large files.
**Details:** We will build the `/api/documents/upload` endpoint. The service layer will handle receiving the file stream, validating file types (PDF, txt, md), and securely writing the chunks to disk using `Path.relative_to()` to strictly prevent Path Traversal attacks. We will implement generator-based reading utilities to parse the text without loading the entire document into memory. This cycle ensures that the application is secure against basic malicious inputs and handles I/O operations safely asynchronously.
**Deliverables:** `src/api/routers/documents.py`, `src/services/file_processing.py`.

### Cycle 04: AI Preprocessing & Semantic Chunking Engine
**Goal:** Implement the LangGraph-based workflow for semantic chunking and entity extraction.
**Details:** We will create a stateful graph using LangGraph in `src/services/ingestion_workflow.py`. The first nodes in this graph will handle taking the text stream, prompting the LLM (via the injected `ILLMProvider`) to identify proposition boundaries, and splitting the text into `DocumentChunk` objects. Concurrently, it will extract entities and metadata (time axis, logic axis tags) to attach to these chunks. We will ensure robust error handling and prompt caching utilization.
**Deliverables:** `src/services/ingestion_workflow.py` (Chunking Logic), integrated with LLM prompts.

### Cycle 05: RAPTOR Tree Generation & Chain of Density (CoD)
**Goal:** Build the hierarchical knowledge tree and apply high-density summarization.
**Details:** Continuing the LangGraph workflow, we will implement the RAPTOR logic. The service will embed the chunks, perform soft clustering (simulated or via lightweight algorithms), and generate hierarchical `ConceptNode` objects. Each node's text will be passed through a Chain of Density (CoD) prompt iteration to maximize information density while maintaining character limits. The resulting tree will be persisted in the vector store and metadata database.
**Deliverables:** `src/services/raptor_builder.py`, `src/services/cod_summarizer.py`, integration into the ingestion LangGraph.

### Cycle 06: Interactive Learning API (Question & Recite)
**Goal:** Implement the core SQ3R backend APIs for generating questions, validating answers, and evaluating user audio recitations.
**Details:** We will build endpoints for fetching the tree structure (Survey) and requesting access to a locked node. The service will dynamically generate context-aware questions based on user level. We will implement the `Recite` endpoint, which accepts text (converted from audio by the frontend or external API), uses the Context-Aware Hierarchical Merging (CAHM) algorithm to check the user's input against the original facts in the vector DB, and returns a "Sandwich Feedback" response indicating success, hallucination, or minor misunderstandings.
**Deliverables:** `src/api/routers/study.py`, `src/services/interactive_tutor.py`.

### Cycle 07: Pivot KJ Engine & Multi-Dimensional Analysis
**Goal:** Implement the multi-dimensional knowledge restructuring feature and Web-Grounding verification.
**Details:** We will implement the `Pivot KJ` service. This service takes a document ID and a requested `AnalysisAxis` (e.g., SWOT, System Design). It queries the vector database using the pre-calculated metadata tags and uses an advanced reasoning LLM to map the `ConceptNode` objects into a new `PivotBoard` structure. We will implement the Web-Grounding logic, allowing the AI to optionally cross-reference the generated structure with external best practices or facts to suggest bias removal.
**Deliverables:** `src/services/kj_analyzer.py`, API endpoints for Pivot in `src/api/routers/export.py`.

### Cycle 08: Output Generation & System Polish
**Goal:** Implement automated document and diagram export, finalize configurations, and perform full system validation.
**Details:** Based on the reordered `PivotBoard`, we will implement generators that format the data into a structured Markdown Document (e.g., PRD) and extract Mermaid.js code snippets representing sequence diagrams, state machines, or workflows. We will finalize all dependency wiring, ensure the OpenRouter BYOK configuration flows securely from the client request to the infrastructure layer, and verify all strict linting and test coverage requirements are met.
**Deliverables:** `src/services/export_generator.py`, final API integration, and comprehensive system polishing.

## 6. Test Strategy
Testing is fundamental and strictly dictates the development flow. The target coverage for all modules is 80% minimum. To prevent side-effects, we will heavily utilize `unittest.mock.AsyncMock`, temporary directories, and `pytest.MonkeyPatch`. A `TestConfigFactory` in `conftest.py` will supply dynamic settings using UUIDs to prevent state leakage between tests.

### Cycle 01: Core Infrastructure & Domain Scaffolding
**Strategy:** We will write Unit Tests for all Pydantic models to ensure validation logic (e.g., `extra="forbid"`, type constraints) works as expected. We will test the `BaseSettings` instantiation using `monkeypatch.setenv` to verify it correctly reads environment variables and falls back to safe defaults or raises validation errors when required variables are missing. There are no side-effects here as no external systems are contacted.

### Cycle 02: Infrastructure Adapters Implementation
**Strategy:** We will test the `OpenRouterClient` by mocking the `httpx.AsyncClient.post` method, returning predefined JSON fixtures representing LLM responses. We will verify that connection pooling logic is correctly initialized and closed. For `local_storage`, we will use `pytest`'s built-in `tmp_path` fixture to write and read files in a temporary directory, ensuring that `aiofiles` handles binary streams without throwing errors and safely decodes UTF-8 without corruption.

### Cycle 03: Document Ingestion & Safe File Handling
**Strategy:** We will perform Integration Testing on the FastAPI endpoints using `httpx.AsyncClient` connected to the FastAPI test app. We will upload mock text files generated in-memory (using multiplied byte arrays to simulate large files without real OOM risks). We will test security rules by attempting to upload a file with a path like `../../etc/passwd` to ensure the `Path.relative_to()` boundary validation explicitly rejects it with a 400 Bad Request.

### Cycle 04: AI Preprocessing & Semantic Chunking Engine
**Strategy:** We will test the LangGraph state machine execution by injecting a mock `ILLMProvider` that returns deterministic responses. We will verify that given a long string of text, the graph correctly transitions through the nodes, queries the LLM mock exactly the expected number of times, and outputs a list of `DocumentChunk` objects with correctly populated metadata. The test will not make any real network calls.

### Cycle 05: RAPTOR Tree Generation & Chain of Density (CoD)
**Strategy:** We will provide an artificial list of `DocumentChunk` objects to the RAPTOR builder service. We will mock the embedding generation and clustering functions to return predictable cluster groups. We will then verify that the service correctly constructs a hierarchical parent-child relationship between `ConceptNode` objects. We will test the CoD loop by asserting that the LLM mock is called sequentially the correct number of times per node, simulating the density refinement process.

### Cycle 06: Interactive Learning API (Question & Recite)
**Strategy:** We will write Unit Tests for the CAHM algorithm. We will supply a known "ground truth" chunk and a simulated user audio transcript. We will assert that the service accurately classifies the input as "correct", "hallucination", or "partial" based on predefined mocked LLM reasoning outputs. We will also test the `/study` API endpoints, verifying that locked nodes successfully return HTTP 403 or specific lock metadata, and only unlock when the correct payload is submitted.

### Cycle 07: Pivot KJ Engine & Multi-Dimensional Analysis
**Strategy:** We will mock the `IVectorStore` to return a specific subset of tagged chunks. We will execute the `kj_analyzer` service and verify that it correctly bins the chunks into the specified dimensions (e.g., placing all "Actor" tags into one cluster, and "State" tags into another). We will test the Web-Grounding feature by ensuring it safely catches exceptions if the external search API mock throws a timeout, gracefully falling back to returning the unverified KJ board.

### Cycle 08: Output Generation & System Polish
**Strategy:** We will run End-to-End (E2E) tests simulating a complete user journey: uploading a mock document, querying the tree, running a Pivot KJ analysis, and requesting an export. The entire external infrastructure (LLMs, VectorDB) will be mocked out at the Dependency Injection container level. We will assert that the final generated Markdown contains the expected structure, valid Mermaid snippet blocks, and that the entire pipeline completes without memory leaks or unhandled exceptions. We will also execute `uv run pytest --cov` to ensure the 80% coverage mandate is strictly satisfied.
