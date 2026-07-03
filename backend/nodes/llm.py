"""LLM node handler."""

from pydantic import ValidationError

from db.repositories import LLMProviderRepository
from exceptions import ExecutionGraphValidationError
from llm import create_llm_client
from nodes.base import NodeExecutionContext
from schemas import ChatMessage, GenerationParams, LLMProviderResponse
from utils.encryption import decrypt

_GENERATION_PARAM_FIELDS = ("temperature", "max_tokens", "top_p")


def _build_generation_params(
    node_data: dict[str, object],
) -> GenerationParams | None:
    """Build generation params from node data.

    Args:
        node_data: Raw node configuration.

    Returns:
        Parsed generation params, or None when none are configured.

    Raises:
        ExecutionGraphValidationError: If a configured value is invalid.

    """
    provided = {
        field: node_data[field]
        for field in _GENERATION_PARAM_FIELDS
        if node_data.get(field) is not None
    }
    if not provided:
        return None

    try:
        return GenerationParams.model_validate(provided)
    except ValidationError as exc:
        message = "LLM node has invalid generation parameters"
        raise ExecutionGraphValidationError(message=message) from exc


class LLMNodeHandler:
    """Handler for LLM nodes."""

    def __init__(self, llm_provider_repository: LLMProviderRepository) -> None:
        """Initialize handler dependencies.

        Args:
            llm_provider_repository: Repository for LLM provider lookups.

        """
        self._llm_provider_repository = llm_provider_repository

    async def execute(self, context: NodeExecutionContext) -> str:
        """Run one LLM node.

        Args:
            context: Node execution context.

        Returns:
            LLM output text.

        Raises:
            ExecutionGraphValidationError: If node configuration is invalid.

        """
        llm_provider_id = context.node_data.get("llm_provider_id")
        if not isinstance(llm_provider_id, int) or llm_provider_id <= 0:
            message = "LLM node requires a valid llm_provider_id"
            raise ExecutionGraphValidationError(message=message)

        model = context.node_data.get("model")
        if not isinstance(model, str) or not model:
            message = "LLM node requires a non-empty model"
            raise ExecutionGraphValidationError(message=message)

        system_prompt_value = context.node_data.get("system_prompt", "")
        if not isinstance(system_prompt_value, str):
            message = "LLM node field system_prompt must be a string"
            raise ExecutionGraphValidationError(message=message)

        params = _build_generation_params(context.node_data)

        llm_provider = await self._llm_provider_repository.get_by(
            session=context.session,
            id=llm_provider_id,
            user_id=context.workflow_owner_id,
        )
        if llm_provider is None:
            message = "Referenced LLM provider does not exist"
            raise ExecutionGraphValidationError(message=message)

        api_key = decrypt(llm_provider.api_key) if llm_provider.api_key else None
        client = create_llm_client(
            llm_provider=LLMProviderResponse.model_validate(llm_provider),
            api_key=api_key,
        )
        messages = [
            ChatMessage(role="system", content=system_prompt_value),
            ChatMessage(role="user", content="\n".join(context.parent_values)),
        ]

        if context.on_token is None:
            response = await client.chat(model=model, messages=messages, params=params)
            return response.message.content

        chunks: list[str] = []
        async for delta in client.stream_chat(
            model=model, messages=messages, params=params
        ):
            chunks.append(delta)
            await context.on_token(delta)

        return "".join(chunks)
