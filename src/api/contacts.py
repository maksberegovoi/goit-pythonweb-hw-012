from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.database.models import User
from src.schemas.contacts import ContactCreate, ContactUpdate, ContactResponse
from src.services.auth import get_current_user
from src.services.contacts import ContactService


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=ContactResponse,status_code=status.HTTP_201_CREATED)
async def create(contact: ContactCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
       Create a new contact for the authenticated user.

       Args:
           contact (ContactCreate): Data required to create a contact.
           user (User): The currently authenticated user (injected by dependency).
           db (AsyncSession): Database session (injected by dependency).

       Returns:
           ContactResponse: The created contact.
       """
    service = ContactService(db)
    return await service.create_contact(contact.model_dump(), user)

@router.get("/", response_model=list[ContactResponse])
async def list_contacts(q: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
        Retrieve a list of contacts for the authenticated user, optionally filtered by a search query.

        Args:
            q (str | None): Optional search query to filter contacts.
            user (User): The currently authenticated user (injected by dependency).
            db (AsyncSession): Database session (injected by dependency).

        Returns:
            list[ContactResponse]: List of contacts matching the search query.
        """
    service = ContactService(db)
    return await service.list_contacts(user, q)

@router.get("/{contact_id}", response_model=ContactResponse)
async def get(contact_id: int, db: AsyncSession = Depends(get_db)):
    """
        Retrieve a single contact by its ID.

        Args:
            contact_id (int): ID of the contact to retrieve.
            db (AsyncSession): Database session (injected by dependency).

        Raises:
            HTTPException: If the contact does not exist (status code 404).

        Returns:
            ContactResponse: The requested contact.
        """
    service = ContactService(db)
    contact = await service.get_contact(contact_id)
    if not contact:
        raise HTTPException(404)
    return contact

@router.patch("/{contact_id}", response_model=ContactResponse, status_code=status.HTTP_200_OK)
async def update(contact_id: int, data: ContactUpdate, db: AsyncSession = Depends(get_db)):
    """
        Update an existing contact by its ID.

        Args:
            contact_id (int): ID of the contact to update.
            data (ContactUpdate): Fields to update in the contact.
            db (AsyncSession): Database session (injected by dependency).

        Raises:
            HTTPException: If the contact does not exist (status code 404).

        Returns:
            ContactResponse: The updated contact.
        """
    service = ContactService(db)
    contact = await service.get_contact(contact_id)
    if not contact:
        raise HTTPException(404)
    return await service.update_contact(contact, data.model_dump())

@router.delete("/{contact_id}", status_code=status.HTTP_200_OK)
async def delete(contact_id: int, db: AsyncSession = Depends(get_db)):
    """
        Delete a contact by its ID.

        Args:
            contact_id (int): ID of the contact to delete.
            db (AsyncSession): Database session (injected by dependency).

        Raises:
            HTTPException: If the contact does not exist (status code 404).

        Returns:
            dict: Status message confirming deletion.
        """
    service = ContactService(db)
    contact = await service.get_contact(contact_id)
    if not contact:
        raise HTTPException(404)
    await service.delete_contact(contact)
    return {"status": "deleted"}

@router.get("/birthdays/next", response_model=list[ContactResponse])
async def birthdays(db: AsyncSession = Depends(get_db)):
    """
       Retrieve a list of contacts who have upcoming birthdays.

       Args:
           db (AsyncSession): Database session (injected by dependency).

       Returns:
           list[ContactResponse]: List of contacts with upcoming birthdays.
       """
    service = ContactService(db)
    return await service.birthdays()
