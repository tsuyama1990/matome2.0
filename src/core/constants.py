"""Centralized constants for the application."""

# Domain-level constants not related to configuration should reside here.
API_KEY_REGEX_PATTERN = r"^sk-or-v1-[a-zA-Z0-9_]+$"

# Vector Store Errors
ERR_PINECONE_ADAPTER_UPSERT_01 = "ERR_PINECONE_ADAPTER_UPSERT_01"
ERR_PINECONE_ADAPTER_QUERY_01 = "ERR_PINECONE_ADAPTER_QUERY_01"
ERR_PINECONE_ADAPTER_STATS_01 = "ERR_PINECONE_ADAPTER_STATS_01"
ERR_INVALID_PINECONE_API_KEY_FORMAT = "ERR_INVALID_PINECONE_API_KEY_FORMAT"
ERR_PINECONE_UPSERT_01 = "ERR_PINECONE_UPSERT_01"
ERR_PINECONE_SEARCH_01 = "ERR_PINECONE_SEARCH_01"
ERR_INVALID_OR_MISSING_EMBEDDING = "Chunk {chunk_id} has invalid or missing embedding"
ERR_EMPTY_EMBEDDING = "Chunk {chunk_id} has empty embedding"
ERR_EMBEDDING_MUST_BE_LIST = "query_embedding must be a valid list"
ERR_EMBEDDING_CANNOT_BE_EMPTY = "query_embedding cannot be empty"
ERR_EMBEDDING_MUST_BE_NUMERIC = "query_embedding must contain only numeric values"
ERR_BATCH_SIZE_EXCEEDED = "Batch size exceeds maximum allowed ({max_batch_size})"
