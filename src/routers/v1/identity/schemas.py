"""Identity schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, description="Username")
    email: EmailStr = Field(..., description="Email address")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password")


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True
