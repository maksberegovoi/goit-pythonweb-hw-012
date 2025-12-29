from pydantic import BaseModel, EmailStr, ConfigDict

from src.database.models import UserRole


class UserBase(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar_url: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    avatar_url: str | None
    is_verified: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class RequestEmail(BaseModel):
    email: EmailStr

class UserForgotPassword(BaseModel):
    user_data: str | EmailStr
    old_password: str
    new_password: str