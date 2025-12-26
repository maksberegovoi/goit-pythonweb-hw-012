from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.core.limiter import limiter
from src.database.db import get_db
from src.database.models import User
from src.schemas.users import UserBase, UserResponse
from src.services.auth import get_current_user
from src.services.upload_file import UploadFileService
from src.services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserBase)
@limiter.limit("5/minute")
async def me(request: Request, user: UserBase = Depends(get_current_user)):
    return user

@router.patch("/me/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    avatar_url = UploadFileService(
        config.CLOUDINARY_NAME, config.CLOUDINARY_API_KEY, config.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user
