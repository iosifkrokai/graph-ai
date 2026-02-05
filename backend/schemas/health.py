"""Schemas for health check responses."""

from pydantic import BaseModel, Field, computed_field


class ServiceHealthResponse(BaseModel):
    """Response model for an individual service health check."""

    name: str = Field(description="Service name")
    status: bool = Field(description="Service status")


class HealthResponse(BaseModel):
    """Response model for overall health status."""

    services: list[ServiceHealthResponse] = Field(
        default_factory=list, description="Services health status"
    )

    @computed_field
    def status(self) -> bool:
        """Return aggregated health status."""
        return all(service.status for service in self.services)
