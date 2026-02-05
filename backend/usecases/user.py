"""Usecase logic for users."""

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import ConflictError, ResourceNotFoundError
from repositories import UserRepository
from schemas import UserCreate, UserResponse, UserUpdate
from utils.security import hash_password


class UserUsecase:
    """Usecase operations for users."""

    def __init__(self) -> None:
        """Initialize repositories for user operations."""
        self._repository = UserRepository()

    async def create_user(
        self, session: AsyncSession, data: UserCreate
    ) -> UserResponse:
        """Create a new user."""
        existing = await self._repository.get_by(session=session, email=data.email)
        if existing:
            message = "User with this email already exists"
            raise ConflictError(message)

        user = await self._repository.create(
            session=session,
            data={
                "email": data.email,
                "hashed_password": hash_password(data.password),
            },
        )
        return UserResponse.model_validate(user)

    async def get_users(self, session: AsyncSession) -> list[UserResponse]:
        """List all users."""
        return [
            UserResponse.model_validate(user)
            for user in await self._repository.get_all(session=session)
        ]

    async def get_user(self, session: AsyncSession, user_id: int) -> UserResponse:
        """Fetch a user by ID."""
        user = await self._repository.get_by(session=session, id=user_id)
        if not user:
            resource = "User"
            raise ResourceNotFoundError(resource)
        return UserResponse.model_validate(user)

    async def update_user(
        self, session: AsyncSession, user_id: int, data: UserUpdate
    ) -> UserResponse:
        """Update a user by ID."""
        user = await self._repository.get_by(session=session, id=user_id)
        if not user:
            resource = "User"
            raise ResourceNotFoundError(resource)

        update_data: dict[str, object] = {}
        if data.email is not None:
            existing = await self._repository.get_by(session=session, email=data.email)
            if existing and existing.id != user_id:
                message = "User with this email already exists"
                raise ConflictError(message)
            update_data["email"] = data.email
        if data.password is not None:
            update_data["hashed_password"] = hash_password(data.password)

        if not update_data:
            return UserResponse.model_validate(user)

        updated = await self._repository.update_by(
            session=session,
            data=update_data,
            id=user_id,
        )
        if not updated:
            resource = "User"
            raise ResourceNotFoundError(resource)
        return UserResponse.model_validate(updated)

    async def delete_user(self, session: AsyncSession, user_id: int) -> None:
        """Delete a user by ID."""
        deleted = await self._repository.delete_by(session=session, id=user_id)
        if not deleted:
            resource = "User"
            raise ResourceNotFoundError(resource)
