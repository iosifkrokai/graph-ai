"""Auth-related API schemas."""

from pydantic import BaseModel, EmailStr, Field


class Login(BaseModel):
    """Login payload."""

    email: EmailStr = Field(default=..., description="Email of the user")
    password: str = Field(default=..., description="Password of the user")


class Token(BaseModel):
    """Access token response."""

    access_token: str = Field(default=..., description="Access token")
    token_type: str = Field(default=..., description="Token type")
