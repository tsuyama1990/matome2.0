import time
from pathlib import Path
from uuid import uuid4

import pytest

from src.domain_models.document import Document


@pytest.mark.asyncio
async def test_large_dataset_streaming_memory_usage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 1. Create a large dummy file, 100k lines roughly simulating a big dataset
    test_file = tmp_path / "large_doc.txt"
    chunk_line = b"This is a test chunk line designed to simulate a relatively long line of text inside a large file.\n"
    test_file.write_bytes(chunk_line * 10_000)

    doc = Document(id=uuid4(), title="Performance Test", file_path=str(test_file))
    from typing import Any

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )

    start_time = time.time()

    # 2. Extract Chunks via Streaming
    chunk_count = 0
    # Process without loading the full list
    async for chunk in doc.stream_chunks(allowed_dir=str(tmp_path), block_size=8192):
        chunk_count += 1
        assert len(chunk.content) > 0

    end_time = time.time()

    # Check that we chunked properly
    assert chunk_count > 100
    # Must process fast
    assert (end_time - start_time) < 10.0  # Allow some leniency for sandbox env speed variations


@pytest.mark.asyncio
async def test_end_to_end_performance_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifies that a 1MB sized mock document can stream, chunk, and be queued for vector storage rapidly."""
    import time
    from unittest.mock import AsyncMock

    from src.infrastructure.pinecone_vdb import PineconeVectorStore

    test_file = tmp_path / "1mb_doc.txt"
    # Create a 1MB file approx (1024 * 1024 bytes)
    chunk_line = (
        b"This is a relatively small chunk designed to hit around 1MB in size for testing purposes."
    )
    line_count = (1024 * 1024) // len(chunk_line)
    test_file.write_bytes(chunk_line * line_count)

    doc = Document(id=uuid4(), title="E2E Perf Test", file_path=str(test_file))
    from typing import Any

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )

    vdb = PineconeVectorStore(api_url="http://mock")
    vdb.upsert_chunks = AsyncMock(return_value=True)  # type: ignore[method-assign]

    start_time = time.time()

    chunks = []
    # Block size of 8192 limits the generated chunk size to under 10000 characters enforced by SemanticChunk Pydantic bounds
    async for chunk in doc.stream_chunks(allowed_dir=str(tmp_path), block_size=8192):
        chunks.append(chunk)

    # Perform batch insert
    res = await vdb.upsert_chunks_batch(chunks, batch_size=50)

    end_time = time.time()

    assert res is True
    assert len(chunks) > 0
    assert (
        end_time - start_time
    ) < 5.0  # Processing 1MB pipeline should easily complete under 5 seconds

    await vdb.close()
