from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar_url: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


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