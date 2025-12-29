from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class ContactBase(BaseModel):
    name: str
    surname: str
    email: EmailStr
    phone: str
    birthday: date
    info: str | None = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    birthday: Optional[str]
    info: Optional[str]

class ContactResponse(ContactBase):
    id: int

    class Config:
        from_attributes = True
