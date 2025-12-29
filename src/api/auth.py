from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.core.limiter import limiter
from src.database.db import get_db
from src.database.models import User
from src.schemas.users import UserBase, UserCreate, Token, RequestEmail, \
    UserForgotPassword
from src.services.auth import Hash, create_access_token
from src.services.email import send_email_for_confirm,send_email_for_reset_password
from src.services.users import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

# Реєстрація користувача
@router.post("/registration", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, background_tasks: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    """
        Register a new user.

        Args:
            user_data (UserCreate): User registration data.
            background_tasks (BackgroundTasks): Background tasks handler.
            request (Request): Incoming HTTP request.
            db (AsyncSession): Database session (injected by dependency).

        Raises:
            HTTPException: If a user with the given email already exists (status 409).

        Returns:
            UserBase: The created user data.
        """

    user_service = UserService(db)

    is_user = await user_service.get_user_by_email(user_data.email)
    if is_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User has already exist'
        )


    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email_for_confirm, new_user.email, new_user.username, request.base_url
    )

    return new_user


@router.post('/login', response_model=Token)
async def login_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """
        Authenticate a user and return a JWT access token.

        Args:
            form_data (OAuth2PasswordRequestForm): Login credentials.
            db (AsyncSession): Database session (injected by dependency).

        Raises:
            HTTPException: If the email is not verified or credentials are invalid (status 401).

        Returns:
            dict: Access token and token type.
        """

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
    """
        Confirm a user's email using a verification token.

        Args:
            token (str): Email verification JWT token.
            db (AsyncSession): Database session (injected by dependency).

        Raises:
            HTTPException: If token is invalid or user does not exist (status 400).

        Returns:
            dict: Message indicating the email verification status.
        """

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
    """
       Decode a JWT token to extract the email.

       Args:
           token (str): JWT token.

       Raises:
           HTTPException: If token is invalid (status 422).

       Returns:
           str: Email extracted from the token.
       """
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
    """
        Request a new email confirmation for an existing user.

        Args:
            body (RequestEmail): Email address for confirmation.
            background_tasks (BackgroundTasks): Background tasks handler.
            request (Request): Incoming HTTP request.
            db (AsyncSession): Database session (injected by dependency).

        Returns:
            dict: Message indicating confirmation email status.
        """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    if user:
        background_tasks.add_task(
            send_email_for_confirm, user.email, user.username, request.base_url
        )
    return {"message": "Перевірте свою електронну пошту для підтвердження"}


@router.post("/forgot_password", status_code=status.HTTP_200_OK)
@limiter.limit("1/minute")
@limiter.limit("3/day")
async def forgot_password(
        data: UserForgotPassword, background_tasks: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)
):
    """
        Initiate password reset process for a user by verifying old password and sending confirmation email.

        Args:
            data (UserForgotPassword): Old and new password data.
            background_tasks (BackgroundTasks): Background tasks handler.
            request (Request): Incoming HTTP request.
            db (AsyncSession): Database session (injected by dependency).

        Raises:
            HTTPException: If user does not exist, old password is incorrect, or new password is same as current.

        Returns:
            dict: Message indicating the next step for password reset.
        """
    user_service = UserService(db)
    user: User = await user_service.get_user_by_email(data.user_data)
    print(data)
    if not user:
        user = await user_service.get_user_by_username(data.user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User does not exist'
            )


    if not Hash().verify_password(data.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Incorrect old password'
        )

    if data.new_password == user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='New password must be different from the current password'
        )
    temp_pass_hashed = Hash.get_password_hash(data.new_password)
    await user_service.set_temp_password(temp_pass_hashed, user.email)
    background_tasks.add_task(
        send_email_for_reset_password, user.email, user.username, request.base_url
    )

    return {"message": "Check your email to confirm new password"}

@router.get("/reset_password/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
       Complete password reset process by verifying token and setting new password.

       Args:
           token (str): Password reset JWT token.
           db (AsyncSession): Database session (injected by dependency).

       Raises:
           HTTPException: If token is invalid or user does not exist (status 400).

       Returns:
           dict: Message indicating password has been successfully changed.
       """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )

    await user_service.set_new_password(user.temp_password, user.email)
    await user_service.set_temp_password(None, user.email)
    return {"message": "Password successfully changed"}