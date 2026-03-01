from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain_models.chunk import SemanticChunk
from src.domain_models.document import Document
from src.infrastructure.pinecone_vdb import PineconeVectorStore


@pytest.mark.asyncio
async def test_full_pipeline_ingestion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. Create dummy file
    test_file = tmp_path / "test_doc.txt"
    test_file.write_text("Hello\nWorld\nIntegration\nTest")

    doc = Document(id=uuid4(), title="Int Test", file_path=str(test_file))
    from typing import Any

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )

    # 2. Extract Chunks
    chunks: list[SemanticChunk] = []
    async for chunk in doc.stream_chunks(allowed_dir=str(tmp_path), block_size=10):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert chunks[0].document_id == doc.id

    # 3. Batch insert into VDB
    vdb = PineconeVectorStore(api_url="http://test")

    # We mock the upsert_chunks as pinecone is an external API
    vdb.upsert_chunks = AsyncMock(return_value=True)  # type: ignore[method-assign]

    res = await vdb.upsert_chunks_batch(chunks, batch_size=2)

    assert res is True
    assert vdb.upsert_chunks.call_count == (len(chunks) + 1) // 2

    # Verify that the correct chunks are being passed into the mock
    called_chunks = vdb.upsert_chunks.call_args[0][0]
    assert len(called_chunks) <= 2
    assert isinstance(called_chunks[0], SemanticChunk)
    assert called_chunks[0].document_id == doc.id

    await vdb.close()
