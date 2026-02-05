"""Schemas for user API payloads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """Payload for creating a user."""

    email: str = Field(default=..., description="Email address")
    password: str = Field(default=..., description="Plaintext password")


class UserUpdate(BaseModel):
    """Payload for updating a user."""

    email: str | None = Field(default=None, description="Email address")
    password: str | None = Field(default=None, description="Plaintext password")


class UserResponse(BaseModel):
    """Response model for users."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(default=..., description="User ID", gt=0)
    email: str = Field(default=..., description="Email address")
    created_at: datetime = Field(default=..., description="Created at")
    updated_at: datetime = Field(default=..., description="Updated at")
