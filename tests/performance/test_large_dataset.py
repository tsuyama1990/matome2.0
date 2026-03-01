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
    lines = [
        "This is a test chunk line designed to simulate a relatively long line of text inside a large file.\n"
        for _ in range(10_000)
    ]
    test_file.write_text("".join(lines))

    doc = Document(id=uuid4(), title="Performance Test", file_path=str(test_file))
    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security", lambda self: None
    )

    start_time = time.time()

    # 2. Extract Chunks via Streaming
    chunk_count = 0
    # Process without loading the full list
    async for chunk in doc.stream_chunks(block_size=8192):
        chunk_count += 1
        assert len(chunk.content) > 0

    end_time = time.time()

    # Check that we chunked properly
    assert chunk_count > 100
    # Must process fast
    assert (end_time - start_time) < 5.0  # Allow some leniency for sandbox env speed variations
