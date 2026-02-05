"""Schemas for edge API payloads."""

from pydantic import BaseModel, ConfigDict, Field


class EdgeCreate(BaseModel):
    """Payload for creating an edge."""

    workflow_id: int = Field(default=..., description="Workflow ID", gt=0)
    source_node_id: int = Field(default=..., description="Source node ID", gt=0)
    target_node_id: int = Field(default=..., description="Target node ID", gt=0)


class EdgeUpdate(BaseModel):
    """Payload for updating an edge."""

    source_node_id: int | None = Field(default=None, description="Source node ID")
    target_node_id: int | None = Field(default=None, description="Target node ID")


class EdgeResponse(BaseModel):
    """Response model for edges."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(default=..., description="Edge ID", gt=0)
    workflow_id: int = Field(default=..., description="Workflow ID", gt=0)
    source_node_id: int = Field(default=..., description="Source node ID", gt=0)
    target_node_id: int = Field(default=..., description="Target node ID", gt=0)
