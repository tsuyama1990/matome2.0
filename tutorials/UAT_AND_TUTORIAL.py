import json
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.domain_models.chunk import SemanticChunk
from src.domain_models.document import Document, SourceType
from src.domain_models.node import KnowledgeNode
from src.main import app

client = TestClient(app)


def run_uat() -> None:
    print("Running UAT-C01-01: Verify Core Infrastructure and Data Modeling")
    print("----------------------------------------------------------------")

    print("\n1. Testing valid object instantiation...")
    chunk_id = uuid4()
    node_id = uuid4()
    doc_id = uuid4()

    chunk = SemanticChunk(id=chunk_id, content="Valid chunk content.", embedding=[0.1])
    node = KnowledgeNode(id=node_id, level=0, title="Valid Node", dense_summary="Summary")
    doc = Document(id=doc_id, filename="test.pdf", source_type=SourceType.PDF)

    print(f"✓ Valid SemanticChunk created: {chunk.id}")
    print(f"✓ Valid KnowledgeNode created: {node.id}")
    print(f"✓ Valid Document created: {doc.id}")

    print("\n2. Testing invalid object instantiation (should raise ValidationError)...")
    try:
        KnowledgeNode(id=uuid4(), level=-1, title="Invalid Node", dense_summary="Summary")
    except ValidationError as e:
        print("✓ Caught expected ValidationError for invalid level:")
        print(f"  {json.loads(e.json())[0]['msg']}")

    try:
        SemanticChunk(id=uuid4(), content="   ")
    except ValidationError as e:
        print("✓ Caught expected ValidationError for empty content:")
        print(f"  {json.loads(e.json())[0]['msg']}")

    print("\n3. Testing /health endpoint...")
    response = client.get("/health")
    if response.status_code == 200 and response.json() == {"status": "ok"}:
        print("✓ API /health check passed (200 OK)")
    else:
        print(f"✗ API /health check failed: {response.status_code} - {response.text}")


if __name__ == "__main__":
    run_uat()
