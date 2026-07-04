"""Local CPU embeddings via fastembed.

Model inference is CPU-blocking; callers must run ``embed_texts`` through
``asyncio.to_thread`` rather than awaiting it directly.
"""

import threading

from fastembed import TextEmbedding

from settings import rag_settings

_model: TextEmbedding | None = None
_model_lock = threading.Lock()


def _get_model() -> TextEmbedding:
    global _model  # noqa: PLW0603
    model = _model
    if model is None:
        with _model_lock:
            model = _model
            if model is None:
                model = TextEmbedding(
                    model_name=rag_settings.embedding_model,
                    cache_dir=rag_settings.embedding_cache_dir,
                )
                _model = model
    return model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, blocking the calling thread."""
    model = _get_model()
    return [vector.tolist() for vector in model.embed(texts)]
