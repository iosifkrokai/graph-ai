"""OpenAI-compatible LLM client."""

import contextlib
from collections.abc import AsyncIterator, Iterator

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from exceptions import LLMProviderConfigError, LLMProviderConnectionError
from llm.base import BaseLLMClient
from schemas.llm_provider import (
    ChatMessage,
    ChatResponse,
    GenerationParams,
    LLMProviderModelResponse,
)


@contextlib.contextmanager
def _wrap_openai_errors() -> Iterator[None]:
    """Translate OpenAI SDK errors into domain exceptions.

    Yields:
        Control to the wrapped request block.

    Raises:
        LLMProviderConfigError: If the provider rejects the request as invalid.
        LLMProviderConnectionError: If the provider is unreachable or transient.

    """
    try:
        yield
    except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
        raise LLMProviderConfigError(
            message="OpenAI provider rejected the API key"
        ) from exc
    except openai.BadRequestError as exc:
        raise LLMProviderConfigError(
            message=f"OpenAI provider rejected the request: {exc.message[:300]}"
        ) from exc
    except openai.APIStatusError as exc:
        raise LLMProviderConnectionError(
            message=f"OpenAI provider returned {exc.status_code}"
        ) from exc
    except openai.APIError as exc:
        raise LLMProviderConnectionError(
            message="OpenAI provider is unreachable"
        ) from exc


def _temperature(params: GenerationParams | None) -> float | openai.Omit:
    """Resolve the temperature argument or an omit sentinel."""
    if params is not None and params.temperature is not None:
        return params.temperature
    return openai.omit


def _max_tokens(params: GenerationParams | None) -> int | openai.Omit:
    """Resolve the max_tokens argument or an omit sentinel."""
    if params is not None and params.max_tokens is not None:
        return params.max_tokens
    return openai.omit


def _top_p(params: GenerationParams | None) -> float | openai.Omit:
    """Resolve the top_p argument or an omit sentinel."""
    if params is not None and params.top_p is not None:
        return params.top_p
    return openai.omit


def _to_openai_messages(
    messages: list[ChatMessage],
) -> list[ChatCompletionMessageParam]:
    """Translate chat messages into typed OpenAI message params.

    Args:
        messages: Ordered chat messages.

    Returns:
        OpenAI chat message params.

    """
    result: list[ChatCompletionMessageParam] = []
    for message in messages:
        if message.role == "system":
            result.append(
                ChatCompletionSystemMessageParam(role="system", content=message.content)
            )
        elif message.role == "assistant":
            result.append(
                ChatCompletionAssistantMessageParam(
                    role="assistant", content=message.content
                )
            )
        else:
            result.append(
                ChatCompletionUserMessageParam(role="user", content=message.content)
            )
    return result


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI and OpenAI-compatible chat completion APIs."""

    def __init__(
        self,
        base_url: str | None,
        api_key: str,
        timeout: float,
    ) -> None:
        """Initialize the client.

        Args:
            base_url: Base URL override; None uses the OpenAI default endpoint.
            api_key: API key for authentication.
            timeout: Request timeout in seconds.

        """
        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    async def list_models(self) -> list[LLMProviderModelResponse]:
        """List available models from provider.

        Returns:
            Model metadata list.

        Raises:
            LLMProviderConfigError: If the provider rejects the request.
            LLMProviderConnectionError: If the provider is unreachable.

        """
        with _wrap_openai_errors():
            page = await self._client.models.list()

        return [LLMProviderModelResponse(name=model.id) for model in page.data]

    async def chat(
        self,
        model: str,
        messages: list[ChatMessage],
        params: GenerationParams | None = None,
    ) -> ChatResponse:
        """Send chat messages to provider.

        Args:
            model: Model name.
            messages: Chat messages.
            params: Optional generation parameters.

        Returns:
            Chat response payload.

        Raises:
            LLMProviderConfigError: If the provider rejects the request.
            LLMProviderConnectionError: If the provider is unreachable.

        """
        with _wrap_openai_errors():
            response = await self._client.chat.completions.create(
                model=model,
                messages=_to_openai_messages(messages),
                temperature=_temperature(params),
                max_tokens=_max_tokens(params),
                top_p=_top_p(params),
            )

        choice = response.choices[0]
        return ChatResponse(
            model=response.model,
            message=ChatMessage(
                role=choice.message.role,
                content=choice.message.content or "",
            ),
            done=True,
            raw=response.model_dump(),
        )

    async def stream_chat(
        self,
        model: str,
        messages: list[ChatMessage],
        params: GenerationParams | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat completion text deltas from provider.

        Args:
            model: Model name.
            messages: Chat messages.
            params: Optional generation parameters.

        Yields:
            Text deltas as they arrive.

        Raises:
            LLMProviderConfigError: If the provider rejects the request.
            LLMProviderConnectionError: If the provider is unreachable.

        """
        with _wrap_openai_errors():
            stream = await self._client.chat.completions.create(
                model=model,
                messages=_to_openai_messages(messages),
                temperature=_temperature(params),
                max_tokens=_max_tokens(params),
                top_p=_top_p(params),
                stream=True,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
