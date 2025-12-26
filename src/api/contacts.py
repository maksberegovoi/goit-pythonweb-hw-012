from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.database.models import User
from src.schemas.contacts import ContactCreate, ContactUpdate, ContactResponse
from src.services.auth import get_current_user
from src.services.contacts import ContactService


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=ContactResponse)
async def create(contact: ContactCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ContactService(db)
    print(user)
    return await service.create_contact(contact.model_dump(), user)

@router.get("/", response_model=list[ContactResponse])
async def list_contacts(q: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ContactService(db)
    return await service.list_contacts(user, q)

@router.get("/{contact_id}", response_model=ContactResponse)
async def get(contact_id: int, db: AsyncSession = Depends(get_db)):
    service = ContactService(db)
    contact = await service.get_contact(contact_id)
    if not contact:
        raise HTTPException(404)
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
async def update(contact_id: int, data: ContactUpdate, db: AsyncSession = Depends(get_db)):
    service = ContactService(db)
    contact = await service.get_contact(contact_id)
    if not contact:
        raise HTTPException(404)
    return await service.update_contact(contact, data.model_dump())

@router.delete("/{contact_id}")
async def delete(contact_id: int, db: AsyncSession = Depends(get_db)):
    service = ContactService(db)
    contact = await service.get_contact(contact_id)
    if not contact:
        raise HTTPException(404)
    await service.delete_contact(contact)
    return {"status": "deleted"}

@router.get("/birthdays/next", response_model=list[ContactResponse])
async def birthdays(db: AsyncSession = Depends(get_db)):
    service = ContactService(db)
    return await service.birthdays()
