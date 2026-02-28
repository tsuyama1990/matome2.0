# CYCLE01: SPEC

## 1. Summary
This cycle is dedicated to establishing the foundational structures of the `matome2-0` platform. The primary objective is to define the core domain models using Pydantic V2, configure the FastAPI routing shell, and set up the dependency injection framework. By creating these foundational components first, we ensure that subsequent cycles—which will handle complex AI logic like document ingestion and knowledge tree generation—have a robust, type-safe, and well-tested environment to operate within. This phase deliberately avoids integrating any actual Large Language Models (LLMs) or live Vector Databases (VDBs). Instead, we focus exclusively on the precise definition of our data contracts, abstract interfaces, and application configuration management.

The necessity of this approach stems from the inherent complexity of the system described in the `ALL_SPEC.md`. We are building an application that will process multi-dimensional data (text, vectors, hierarchical graphs, and semantic tags) simultaneously. Without a rigid structural foundation enforcing "illegal states are unrepresentable," the system would quickly become fragile and unmaintainable. The use of Pydantic V2 is non-negotiable; its performance improvements over V1 and its advanced validation features (like custom root validators, discriminated unions, and strict mode typing) are essential for guaranteeing the integrity of the data flowing across the application boundary.

Furthermore, this cycle lays the groundwork for the project's testing strategy. By strictly defining abstract interfaces for external dependencies (e.g., `ILLMProvider` instead of a concrete OpenRouter client), we ensure that the entire core business logic remains easily testable in isolation. We will configure the necessary logging, global exception handling, and application startup/shutdown events to provide a professional-grade observability baseline. Ultimately, the success of this cycle is measured not by user-facing features, but by the establishment of a pristine, high-coverage codebase that allows future development to proceed rapidly and securely, free from the drag of poorly defined data structures or tightly coupled architectural dependencies.

## 2. System Architecture
The system architecture implemented in this cycle forms the bedrock of the entire `matome2-0` backend. It strictly adheres to a layered architectural pattern, explicitly separating the API routing layer, the core domain model layer, the service layer, and the infrastructure layer. This separation of concerns is vital for managing the complexity of the Generative AI pipelines that will be integrated later.

At the outermost layer, we establish the FastAPI application shell within `src/api/routers`. This layer is solely responsible for receiving HTTP requests, validating the incoming JSON payloads against our defined Pydantic models, delegating the business logic to the underlying service layer, and returning the appropriate HTTP status codes and formatted responses. It must contain absolutely no business rules or external API calls. We will create a base router (e.g., `base.py`) that includes fundamental health-check endpoints, allowing infrastructure monitoring tools to verify the API's operational status.

Beneath the routing layer lies the dependency injection mechanism, configured in `src/api/dependencies.py`. This is arguably the most critical architectural decision of the cycle. Instead of services directly instantiating their dependencies (like a specific database client), they will rely on FastAPI's `Depends` functionality to resolve these dependencies at runtime. This allows us to easily inject mock implementations during unit testing or switch between different infrastructure providers (e.g., swapping a local Qdrant instance for a managed Pinecone cluster) without altering a single line of business logic.

The core of the application resides in `src/core`. Here, we define the `models` directory, which houses the Pydantic schemas representing the foundational concepts of our domain: `Document`, `KnowledgeNode`, and `SemanticChunk`. These models act as the absolute source of truth regarding the shape of our data. We also establish `config.py`, which utilizes Pydantic's `BaseSettings` to load and validate environment variables securely. This ensures that the application will refuse to start if critical configuration parameters (like API keys or database URLs) are missing or malformed. Additionally, `exceptions.py` defines a hierarchy of custom domain exceptions (e.g., `NodeNotFoundError`, `InvalidChunkStateError`), which the global exception handler will catch and translate into consistent API error responses.

The service layer (`src/services`) will initially contain only base or abstract classes (`base_service.py`), establishing the patterns for how business logic should be organized in future cycles. Similarly, the infrastructure layer (`src/infrastructure`) will be populated with abstract interfaces (`llm_interface.py`, `vdb_interface.py`) defining the exact contracts that any future concrete implementation must fulfill. For example, `IVectorStore` might dictate `upsert_chunks(chunks: List[SemanticChunk]) -> bool` and `search(query_vector: List[float], limit: int) -> List[SemanticChunk]`. This rigorous adherence to the Dependency Inversion Principle guarantees a flexible, resilient architecture capable of evolving alongside the rapidly changing landscape of Generative AI capabilities.

**Code Blueprints and File Structure for Cycle 01:**
```ascii
matome2-0/
├── src/
│   ├── api/
│   │   ├── routers/
│   │   │   └── **base.py**
│   │   └── **dependencies.py**
│   ├── core/
│   │   ├── models/
│   │   │   ├── **document.py**
│   │   │   ├── **node.py**
│   │   │   └── **chunk.py**
│   │   ├── **config.py**
│   │   └── **exceptions.py**
│   ├── services/
│   │   └── **base_service.py**
│   └── infrastructure/
│       ├── **llm_interface.py**
│       └── **vdb_interface.py**
```

## 3. Design Architecture
The data modeling phase of this cycle is driven entirely by Pydantic V2, focusing on the central entities that will power the application: `Document`, `KnowledgeNode`, and `SemanticChunk`.

The `SemanticChunk` represents the atomic unit of ingested information. It must be modeled with fields for `id` (UUID4), `content` (string), `embedding` (Optional[List[float]]), and `metadata` (Dict[str, Any]). We must implement strict validation to ensure that the content string is never empty and that the embedding array, if present, matches the exact dimensions expected by our downstream vector database configuration.

The `KnowledgeNode` model is the building block of the RAPTOR hierarchical tree. It requires a recursive data structure. The model must include an `id`, a `level` (integer representing its depth in the tree, e.g., 0 for root), a `title` (string), a `dense_summary` (string), a `children` list containing `KnowledgeNode` IDs, and a `source_chunks` list containing `SemanticChunk` IDs. Crucially, we must use Pydantic validators to enforce invariants: a node cannot have a negative level, it cannot be its own child, and the `dense_summary` must adhere to length constraints to support the Progressive Disclosure UI.

The `Document` model acts as the aggregate root for a specific ingested file. It will contain an `id`, `filename`, `source_type` (Enum: PDF, EPUB, MARKDOWN), `ingestion_status` (Enum: PENDING, PROCESSING, COMPLETED, FAILED), and a reference to the `root_node_id` representing the top of the RAPTOR tree for that specific document.

These schemas are designed with an additive mindset. As we progress to future cycles, we will extend these models (e.g., adding `MultiDimensionalTags` to the chunk metadata or `InteractionState` attributes) rather than creating conflicting, overlapping structures. The strict typing enforced by Pydantic will allow `mypy` to statically analyze the entire codebase, catching integration errors before runtime.

## 4. Implementation Approach
The implementation will follow a strict Test-Driven Development (TDD) methodology. We will begin by writing failing unit tests defining the expected behavior and validation rules for our Pydantic models before writing the models themselves.

1. **Initialize Project & Core Models:** Create the `src/core/models` directory. Define `SemanticChunk`, `KnowledgeNode`, and `Document` utilizing `pydantic.BaseModel`. Implement custom validators using the `@model_validator` and `@field_validator` decorators to enforce the domain invariants (e.g., UUID format verification, depth level boundaries). Run the test suite to ensure all validators correctly reject malformed data.
2. **Implement Configuration Management:** Create `src/core/config.py`. Define an `AppSettings` class inheriting from `pydantic_settings.BaseSettings`. This class will define required environment variables like `OPENROUTER_API_KEY` and `VECTOR_DB_URL`. Configure it to read from a `.env` file during local development but fall back to system environment variables in production.
3. **Define Abstract Interfaces:** Create the `src/infrastructure` directory. Define `ILLMProvider` and `IVectorStore` using Python's `abc.ABC` module. Define explicit method signatures with comprehensive type hints (e.g., `async def generate_completion(self, prompt: str) -> str:`). This establishes the contract that concrete implementations in subsequent cycles must fulfill.
4. **Implement Global Error Handling:** Create `src/core/exceptions.py`. Define a base `MatomeAppException` inheriting from the standard `Exception`. Create specific subclasses for anticipated errors (e.g., `ResourceNotFoundError`, `ValidationDomainError`).
5. **Wire FastAPI Application Shell:** In the `src` root (or `src/api`), instantiate the `FastAPI` application object. Add an exception handler that catches `MatomeAppException` and translates it into a standard JSON response containing the error message and an appropriate HTTP status code. Create `src/api/routers/base.py` and implement a simple `GET /health` endpoint returning a 200 OK status. Include this router in the main application instance.
6. **Configure Dependency Injection:** Create `src/api/dependencies.py`. Define functions using `Yield` or returning instances of our abstract interfaces (returning mock implementations for now) that the FastAPI endpoints can depend upon via the `Depends()` mechanism.

## 5. Test Strategy
The testing strategy for this foundational cycle focuses exclusively on Unit Testing to guarantee the structural integrity of our data contracts and the correct configuration of our application shell. We do not require complex integration testing yet, as no external services or multi-step workflows have been implemented.

**Unit Testing Approach:**
We will utilize `pytest` to write comprehensive tests for every Pydantic model defined in `src/core/models`. The primary objective is to verify that illegal states are demonstrably unrepresentable. For the `KnowledgeNode` model, we will write tests that attempt to instantiate the model with negative hierarchy levels, empty titles, or cyclic child references, asserting that a `pydantic.ValidationError` is raised in each case. We will also test valid instantiation to ensure data is correctly parsed and assigned.

For the configuration management (`config.py`), we will utilize `pytest.MonkeyPatch` to simulate various environment variable states. We will test that the application successfully boots when all required variables are present and cleanly raises a configuration error when mandatory variables (like database credentials) are missing. This prevents the application from starting in a broken state in production.

We will write unit tests for the global exception handler by creating a dummy FastAPI endpoint that intentionally raises a custom `MatomeAppException`. Using the `fastapi.testclient.TestClient`, we will issue a request to this endpoint and verify that the response has the correct HTTP status code (e.g., 404 Not Found for a `ResourceNotFoundError`) and that the JSON payload strictly conforms to our established error response schema. We will measure our success using `pytest-cov`, aiming for 100% line coverage across the `src/core` and `src/api/routers/base.py` modules before concluding the cycle. This rigorous unit testing regime ensures that the foundation of the `matome2-0` platform is completely solid.
