"""Vector Ingest node handler.

Chunks the upstream text, embeds each chunk locally via fastembed
(``rag.embeddings``), and upserts the chunks into a Qdrant collection
(``rag.qdrant``). Pairs with the Vector Search node, which reads back from
the same collection. Collection names are free text and shared globally —
no per-user/per-workflow namespacing — and re-ingesting the same text simply
appends duplicate chunks; there's no dedup.
"""

from asyncio import to_thread
from uuid import uuid4

from qdrant_client.http.models import PointStruct

from enums import NodeType, PortType, ValidatorType
from exceptions import ExecutionGraphValidationError
from nodes.base import NodeExecutionContext, NodeExecutionResult
from nodes.definition import NodeDefinition, NodeHandlerDeps
from nodes.rendering import upstream_text
from rag.embeddings import embed_texts
from rag.qdrant import chunk_text, ensure_collection, get_qdrant_client
from schemas import NodeFieldSpec, NodeFieldUI, NodeFieldWidget, NodeGraphSpec


class VectorIngestNodeHandler:
    """Handler for vector-ingest nodes."""

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        """Chunk, embed, and store the upstream text in a Qdrant collection.

        Args:
            context: Node execution context.

        Returns:
            A confirmation message with the number of chunks stored.

        Raises:
            ExecutionGraphValidationError: If the collection field is
                missing, or the upstream text is empty.

        """
        collection = context.node_data.get("collection")
        if not isinstance(collection, str) or not collection.strip():
            message = "Vector Ingest node requires a non-empty collection name"
            raise ExecutionGraphValidationError(message=message)

        chunks = chunk_text(upstream_text(context))
        if not chunks:
            message = "Vector Ingest node received no text to ingest"
            raise ExecutionGraphValidationError(message=message)

        vectors = await to_thread(embed_texts, chunks)
        client = get_qdrant_client()
        await ensure_collection(client, collection, vector_size=len(vectors[0]))
        await client.upsert(
            collection_name=collection,
            points=[
                PointStruct(id=str(uuid4()), vector=vector, payload={"text": chunk})
                for vector, chunk in zip(vectors, chunks, strict=True)
            ],
        )
        return NodeExecutionResult(
            output=f"Ingested {len(chunks)} chunk(s) into '{collection}'."
        )


def _build_handler(deps: NodeHandlerDeps) -> VectorIngestNodeHandler:
    """Build a vector-ingest node handler."""
    del deps
    return VectorIngestNodeHandler()


DEFINITION = NodeDefinition(
    type=NodeType.VECTOR_INGEST,
    label="Vector Ingest",
    icon_key="vector_ingest",
    graph=NodeGraphSpec(
        has_input=True,
        has_output=True,
        input_port=PortType.TEXT,
        output_port=PortType.TEXT,
    ),
    fields=(
        NodeFieldSpec(
            name="label",
            required=True,
            validators={ValidatorType.MIN_LENGTH.value: 1},
            ui=NodeFieldUI(
                widget=NodeFieldWidget.TEXT,
                label="Label",
                placeholder="Vector Ingest label",
            ),
            default="Vector Ingest node",
        ),
        NodeFieldSpec(
            name="collection",
            required=True,
            validators={ValidatorType.MIN_LENGTH.value: 1},
            ui=NodeFieldUI(
                widget=NodeFieldWidget.TEXT,
                label="Collection",
                placeholder="my-documents",
                help="Qdrant collection to store chunks in. Created if missing.",
            ),
            default="",
        ),
    ),
    build_handler=_build_handler,
)
