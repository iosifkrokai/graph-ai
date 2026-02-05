"""Schemas for node-related API payloads."""

from pydantic import BaseModel, ConfigDict, Field

from enums import InputFormat, NodeType, OutputFormat


class NodeCreate(BaseModel):
    """Payload for creating a node."""

    workflow_id: int = Field(default=..., description="Workflow ID", gt=0)
    type: NodeType = Field(default=..., description="Node type")
    position_x: float = Field(default=0.0, description="X position on canvas")
    position_y: float = Field(default=0.0, description="Y position on canvas")


class NodeUpdate(BaseModel):
    """Payload for updating a node."""

    position_x: float | None = Field(default=None, description="X position on canvas")
    position_y: float | None = Field(default=None, description="Y position on canvas")


class NodeResponse(BaseModel):
    """Response model for nodes."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(default=..., description="Node ID", gt=0)
    workflow_id: int = Field(default=..., description="Workflow ID", gt=0)
    type: NodeType = Field(default=..., description="Node type")
    position_x: float = Field(default=..., description="X position on canvas")
    position_y: float = Field(default=..., description="Y position on canvas")


class InputNodeCreate(BaseModel):
    """Payload for creating an input node configuration."""

    node_id: int = Field(default=..., description="Node ID", gt=0)
    format: InputFormat = Field(default=InputFormat.TEXT, description="Input format")


class InputNodeUpdate(BaseModel):
    """Payload for updating an input node configuration."""

    format: InputFormat | None = Field(default=None, description="Input format")


class InputNodeResponse(BaseModel):
    """Response model for input node configurations."""

    model_config = ConfigDict(from_attributes=True)

    node_id: int = Field(default=..., description="Node ID", gt=0)
    format: InputFormat = Field(default=..., description="Input format")


class LLMNodeCreate(BaseModel):
    """Payload for creating an LLM node configuration."""

    node_id: int = Field(default=..., description="Node ID", gt=0)
    llm_provider_id: int = Field(default=..., description="LLM provider ID", gt=0)
    model: str = Field(default=..., description="Model identifier")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=1024, description="Max tokens")


class LLMNodeUpdate(BaseModel):
    """Payload for updating an LLM node configuration."""

    llm_provider_id: int | None = Field(default=None, description="LLM provider ID")
    model: str | None = Field(default=None, description="Model identifier")
    temperature: float | None = Field(default=None, description="Sampling temperature")
    max_tokens: int | None = Field(default=None, description="Max tokens")


class LLMNodeResponse(BaseModel):
    """Response model for LLM node configurations."""

    model_config = ConfigDict(from_attributes=True)

    node_id: int = Field(default=..., description="Node ID", gt=0)
    llm_provider_id: int = Field(default=..., description="LLM provider ID", gt=0)
    model: str = Field(default=..., description="Model identifier")
    temperature: float = Field(default=..., description="Sampling temperature")
    max_tokens: int = Field(default=..., description="Max tokens")


class OutputNodeCreate(BaseModel):
    """Payload for creating an output node configuration."""

    node_id: int = Field(default=..., description="Node ID", gt=0)
    format: OutputFormat = Field(default=OutputFormat.TEXT, description="Output format")


class OutputNodeUpdate(BaseModel):
    """Payload for updating an output node configuration."""

    format: OutputFormat | None = Field(default=None, description="Output format")


class OutputNodeResponse(BaseModel):
    """Response model for output node configurations."""

    model_config = ConfigDict(from_attributes=True)

    node_id: int = Field(default=..., description="Node ID", gt=0)
    format: OutputFormat = Field(default=..., description="Output format")
