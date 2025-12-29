from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Contact, User


class ContactRepository:
    """
      Repository class for managing Contact entities in the database.

      Attributes:
          session (AsyncSession): SQLAlchemy asynchronous session for database operations.
      """
    def __init__(self, session: AsyncSession):
        """
                Initialize the repository with a database session.

                Args:
                    session (AsyncSession): Database session.
                """
        self.session = session

    async def create(self, data: dict, user: User):
        """
                Create a new contact for a specific user.

                Args:
                    data (dict): Contact data.
                    user (User): User to whom the contact belongs.

                Returns:
                    Contact: The created Contact instance.
                """
        contact = Contact(**data, user=user)
        self.session.add(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def get_all(self, user: User, query: str | None = None):
        """
               Retrieve all contacts for a user, optionally filtered by a search query.

               Args:
                   user (User): The user whose contacts are retrieved.
                   query (str | None): Optional search query to filter by name, surname, or email.

               Returns:
                   list[Contact]: List of contacts matching the query.
               """
        stmt = select(Contact).where(Contact.user_id == user.id)
        if query:
            stmt = stmt.where(
                (Contact.name.ilike(f"%{query}%")) |
                (Contact.surname.ilike(f"%{query}%")) |
                (Contact.email.ilike(f"%{query}%"))
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, contact_id: int):
        """
                Retrieve a contact by its ID.

                Args:
                    contact_id (int): ID of the contact.

                Returns:
                    Contact | None: Contact instance if found, otherwise None.
                """
        result = await self.session.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def update(self, contact: Contact, data: dict):
        """
               Update a contact with provided data.

               Args:
                   contact (Contact): Contact instance to update.
                   data (dict): Data to update on the contact.

               Returns:
                   Contact: Updated contact instance.
               """
        for key, value in data.items():
            setattr(contact, key, value)
        await self.session.commit()
        return contact

    async def delete(self, contact: Contact):
        """
                Delete a contact from the database.

                Args:
                    contact (Contact): Contact instance to delete.
                """
        await self.session.delete(contact)
        await self.session.commit()

    async def upcoming_birthdays(self):
        """
                Retrieve contacts with birthdays in the next 7 days.

                Returns:
                    list[Contact]: Contacts with upcoming birthdays.
                """
        today = date.today()
        limit = today + timedelta(days=7)
        stmt = select(Contact).where(Contact.birthday.between(today, limit))
        result = await self.session.execute(stmt)
        return result.scalars().all()