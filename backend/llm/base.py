"""Base LLM client protocol."""

from typing import Protocol

from schemas.llm_provider import (
    ChatMessage,
    ChatResponse,
    GenerationParams,
    LLMProviderModelResponse,
)


class BaseLLMClient(Protocol):
    """Interface for LLM provider clients."""

    async def list_models(self) -> list[LLMProviderModelResponse]:
        """List available models from provider."""

    async def chat(
        self,
        model: str,
        messages: list[ChatMessage],
        params: GenerationParams | None = None,
    ) -> ChatResponse:
        """Send chat messages to provider."""
