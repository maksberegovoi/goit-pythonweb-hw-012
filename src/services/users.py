from libgravatar import Gravatar
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.users import UserRepository
from src.schemas.users import UserCreate


class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def create_user(self, data: UserCreate):
        avatar = None
        try:
            g = Gravatar(data.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repo.create_user(data, avatar)

    async def get_user_by_email(self, email: EmailStr):
        return await self.repo.get_user_by_email(email)

    async def get_user_by_username(self, username: str):
        return await self.repo.get_user_by_username(username)

    async def set_user_verified(self, email: EmailStr):
        return await self.repo.set_user_verified(email)

    async def update_avatar_url(self, email: EmailStr, url: str):
        return await self.repo.update_avatar_url(email, url)
