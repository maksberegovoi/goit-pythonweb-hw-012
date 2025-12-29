from fastapi import APIRouter, Depends, Request, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.core.limiter import limiter
from src.database.db import get_db
from src.database.models import User
from src.schemas.users import UserBase, UserResponse
from src.services.auth import get_current_user, get_current_admin_user
from src.services.upload_file import UploadFileService
from src.services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserBase, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def me(request: Request, user: UserBase = Depends(get_current_user)):
    """
        Retrieve the currently authenticated user's basic information.

        Args:
            request (Request): The incoming HTTP request.
            user (UserBase): The currently authenticated user (injected by dependency).

        Returns:
            UserBase: The authenticated user's data.
        """
    return user

@router.patch("/me/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
       Update the avatar image for the authenticated admin user.

       Args:
           file (UploadFile): The uploaded avatar file.
           user (User): The currently authenticated admin user (injected by dependency).
           db (AsyncSession): Database session (injected by dependency).

       Returns:
           UserResponse: Updated user data including the new avatar URL.
       """
    avatar_url = UploadFileService(
        config.CLOUDINARY_NAME, config.CLOUDINARY_API_KEY, config.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user
