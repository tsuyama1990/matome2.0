from pydantic import UUID4, BaseModel, ConfigDict, Field, model_validator


class KnowledgeNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    level: int = Field(ge=0)
    title: str = Field(..., min_length=1, max_length=512, pattern=r"^[^<>;&]*$")
    dense_summary: str = Field(..., min_length=1, max_length=2048)
    children: list[UUID4] = Field(default_factory=list)
    source_chunks: list[UUID4] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_cyclic_dependency(self) -> "KnowledgeNode":
        if self.id in self.children:
            msg = "Node cannot be its own child"
            raise ValueError(msg)

        # Adding a check that list is unique. Although existence is hard to check here (needs DB)
        # We can at least ensure we don't have duplicate chunk references.
        if len(self.source_chunks) != len(set(self.source_chunks)):
            msg = "Source chunks must be unique"
            raise ValueError(msg)

        if len(self.children) != len(set(self.children)):
            msg = "Children must be unique"
            raise ValueError(msg)

        return self

    @classmethod
    def validate_tree_acyclic(cls, nodes: list["KnowledgeNode"]) -> bool:
        """Validates that a collection of nodes forms a directed acyclic graph (DAG)."""
        graph: dict[UUID4, list[UUID4]] = {node.id: node.children for node in nodes}
        visited: set[UUID4] = set()
        recursion_stack: set[UUID4] = set()

        def is_cyclic(node_id: UUID4) -> bool:
            visited.add(node_id)
            recursion_stack.add(node_id)

            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if is_cyclic(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    return True

            recursion_stack.remove(node_id)
            return False

        node_ids = set(graph.keys())
        for node in nodes:
            if not all(child_id in node_ids for child_id in node.children):
                return False

        return all(not (node.id not in visited and is_cyclic(node.id)) for node in nodes)
