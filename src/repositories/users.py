from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from src.schemas.users import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, data: UserCreate, avatar: str = None) -> User:
        user = User(
            **data.model_dump(exclude_unset=True, exclude={'password'}),
            password=data.password,
            avatar_url=avatar
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user


    async def get_user_by_email(self, email: EmailStr) -> User | None:
        stmt = select(User).where(User.email == email)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()


    async def set_user_verified(self, email: EmailStr) -> None:
        user: User = await self.get_user_by_email(email)
        user.is_verified = True
        await self.session.commit()


    async def update_avatar_url(self, email: EmailStr, url: str) -> User:
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.session.commit()
        await self.session.refresh(user)
        return user
