from datetime import date
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

class ContactUpdate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: int

    class Config:
        from_attributes = True
