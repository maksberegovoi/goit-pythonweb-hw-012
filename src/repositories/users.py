from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from src.schemas.users import UserCreate


class UserRepository:
    """
        Repository class for managing User entities in the database.

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

    async def create_user(self, data: UserCreate, avatar: str = None) -> User:
        """
                Create a new user in the database.

                Args:
                    data (UserCreate): User creation data.
                    avatar (str, optional): URL of the user's avatar. Defaults to None.

                Returns:
                    User: The created User instance.
                """
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
        """
               Retrieve a user by email.

               Args:
                   email (EmailStr): Email address to search for.

               Returns:
                   User | None: User instance if found, otherwise None.
               """
        stmt = select(User).where(User.email == email)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
              Retrieve a user by username.

              Args:
                  username (str): Username to search for.

              Returns:
                  User | None: User instance if found, otherwise None.
              """
        stmt = select(User).where(User.username == username)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()


    async def set_user_verified(self, email: EmailStr) -> None:
        """
              Mark a user's email as verified.

              Args:
                  email (EmailStr): Email address of the user to verify.
              """
        user: User = await self.get_user_by_email(email)
        user.is_verified = True
        await self.session.commit()


    async def update_avatar_url(self, email: EmailStr, url: str) -> User:
        """
               Update the avatar URL of a user.

               Args:
                   email (EmailStr): Email address of the user.
                   url (str): New avatar URL.

               Returns:
                   User: Updated User instance.
               """
        user = await self.get_user_by_email(email)
        user.avatar_url = url
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_new_password(self, password, email) -> None:
        """
                Set a new password for the user.

                Args:
                    password (str): New password (hashed).
                    email (EmailStr): Email address of the user.
                """
        user: User = await self.get_user_by_email(email)
        user.password = password
        await self.session.commit()

    async def set_temp_password(self, password: str | None, email: EmailStr) -> None:
        """
               Set a temporary password for the user (used in password reset flow).

               Args:
                   password (str | None): Temporary password (hashed) or None to clear.
                   email (EmailStr): Email address of the user.
               """
        user: User = await self.get_user_by_email(email)
        user.temp_password = password
        await self.session.commit()