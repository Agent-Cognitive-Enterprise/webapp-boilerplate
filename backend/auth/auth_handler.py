# /auth/auth_handler.py

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import EmailStr, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import get_by_email as get_user_by_email
from models.token_data import TokenData
from models.user import User
from settings import (
    AUTH_SECRET_KEY,
    AUTH_ALGORITHM,
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_ACCESS_NAME,
)
from utils.db import get_session
from utils.password import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

router = APIRouter()


async def authenticate_user(
    session: AsyncSession, email: EmailStr, password: str
) -> User | bool:
    db_user = await get_user_by_email(session=session, email=email)

    if not db_user:
        return False

    if not verify_password(
        plain_password=password, hashed_password=db_user.hashed_password
    ):
        return False

    if not db_user.is_active:
        return False

    return db_user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = access_token_expiry(expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=AUTH_ALGORITHM)


def access_token_expiry(expires_delta: timedelta | None = None) -> datetime:
    return datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def get_credentials_exception():
    return HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_not_authenticated_exception() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def resolve_request_access_token(request: Request, token: str | None = None) -> str | None:
    if token:
        return token

    authorization = request.headers.get("authorization", "")
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() == "bearer" and credentials:
        return credentials.strip()

    return request.cookies.get(COOKIE_ACCESS_NAME)


def decode_access_token_email(token: str) -> str:
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[AUTH_ALGORITHM])
        email = payload.get("sub")
        if not isinstance(email, str):
            raise get_credentials_exception()
        token_data = TokenData(email=email)
    except (JWTError, ValidationError):
        raise get_credentials_exception()

    return token_data.email


async def get_current_user_from_request(
    request: Request,
    session: AsyncSession,
    token: str | None = None,
) -> User:
    resolved_token = resolve_request_access_token(request, token)
    if not resolved_token:
        raise get_not_authenticated_exception()

    db_user = await get_user_by_email(
        session=session,
        email=decode_access_token_email(resolved_token),
    )

    if db_user is None:
        raise get_credentials_exception()

    return db_user


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
):
    return await get_current_user_from_request(
        request=request,
        token=token,
        session=session,
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_admin_user_from_request(
    request: Request,
    session: AsyncSession,
    token: str | None = None,
) -> User:
    current_user = await get_current_user_from_request(
        request=request,
        token=token,
        session=session,
    )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
