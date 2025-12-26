from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.database.db import get_db
from src.database.models import User
from src.schemas.users import UserBase, UserCreate, Token, RequestEmail
from src.services.auth import Hash, create_access_token
from src.services.email import send_email
from src.services.users import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

# Реєстрація користувача
@router.post("/registration", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, background_tasks: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)

    is_user = await user_service.get_user_by_email(user_data.email)
    if is_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User has already exist'
        )

    print("Before hashing:", user_data.password, type(user_data.password),
          len(user_data.password))

    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )

    return new_user


@router.post('/login', response_model=Token)
async def login_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user: User = await user_service.get_user_by_username(form_data.username)

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )


    if not user or not Hash().verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await create_access_token(
        data={'sub': user.username}
    )
    return {'access_token': access_token, 'token_type': 'bearer'}

@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.is_verified:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    await user_service.set_user_verified(email)
    return {"message": "Електронну пошту підтверджено"}

async def get_email_from_token(token: str):
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Неправильний токен для перевірки електронної пошти",
        )

@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Перевірте свою електронну пошту для підтвердження"}