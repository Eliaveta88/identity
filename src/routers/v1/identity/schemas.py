"""Identity schemas."""

from typing import List

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8, max_length=255, description="Password")


class UserResponse(UserBase):
    """User response schema."""

    id: int = Field(..., description="User ID")
    roles: List[str] = Field(default=["user"], description="User roles")

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated list of users."""

    items: List[UserResponse]
    total: int = Field(..., ge=0, description="Total active users")
    skip: int = Field(..., ge=0, description="Pagination offset")
    limit: int = Field(..., ge=1, le=100, description="Page size")


class LoginRequest(BaseModel):
    """Login request."""

    username: str = Field(..., min_length=1, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class LoginResponse(BaseModel):
    """Login response with tokens."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user info")


class RefreshTokenRequest(BaseModel):
    """Refresh token request body."""

    refresh_token: str = Field(..., min_length=1, description="JWT refresh token")


class LogoutResponse(BaseModel):
    """Logout response."""

    status: str = Field(..., description="Logout status")
