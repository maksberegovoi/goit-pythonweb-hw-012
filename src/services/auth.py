import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.conf.config import config
from src.database.models import User, UserRole
from src.database.redis import redis_db
from src.services.users import UserService


class Hash:
    """
        Utility class for password hashing and verification using bcrypt.
        """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """
                Verify a plain password against a hashed password.

                Args:
                    plain_password (str): The plaintext password to verify.
                    hashed_password (str): The hashed password to compare against.

                Returns:
                    bool: True if the password matches, False otherwise.
                """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
                Hash a plaintext password.

                Args:
                    password (str): The plaintext password to hash.

                Returns:
                    str: The hashed password.
                """
        return self.pwd_context.hash(password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """
        Create a JWT access token.

        Args:
            data (dict): The payload data to encode in the token.
            expires_delta (Optional[int]): Expiration time in seconds. Defaults to config.JWT_EXPIRATION_SECONDS.

        Returns:
            str: The encoded JWT token.
        """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(timezone.utc) + timedelta(seconds=config.JWT_EXPIRATION_SECONDS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM
    )
    return encoded_jwt


def create_email_token(data: dict):
    """
        Create a JWT token for email verification.

        Args:
            data (dict): The payload data to encode in the token.

        Returns:
            str: The encoded JWT token valid for 7 days.
        """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
        Retrieve the currently authenticated user from the JWT token or Redis cache.

        Args:
            token (str): JWT bearer token.
            db (AsyncSession): Database session.

        Raises:
            HTTPException: If credentials are invalid or user does not exist.

        Returns:
            User: The authenticated user instance.
        """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],
        )
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    cache_key = f"curr_user:{username}"

    user_id = await redis_db.get(cache_key)

    if user_id:
        result = await db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()
        if user:
            return user

    result = await db.execute(
        select(User).where(User.username == username)
    )
    print('db req')
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    await redis_db.set(cache_key, str(user.id), ex=900)

    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
        Ensure the current user is an admin.

        Args:
            current_user (User): The currently authenticated user.

        Raises:
            HTTPException: If the user is not an admin (status 403).

        Returns:
            User: The current user if they are an admin.
        """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостатньо прав доступу")
    return current_user
