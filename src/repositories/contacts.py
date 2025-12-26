from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Contact, User


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict, user: User):
        contact = Contact(**data, user=user)
        self.session.add(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def get_all(self, user: User, query: str | None = None):
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
        result = await self.session.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def update(self, contact: Contact, data: dict):
        for key, value in data.items():
            setattr(contact, key, value)
        await self.session.commit()
        return contact

    async def delete(self, contact: Contact):
        await self.session.delete(contact)
        await self.session.commit()

    async def upcoming_birthdays(self):
        today = date.today()
        limit = today + timedelta(days=7)
        stmt = select(Contact).where(Contact.birthday.between(today, limit))
        result = await self.session.execute(stmt)
        return result.scalars().all()