import os
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError
from jose import jwt

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from sqlalchemy.orm import Session

import models

from database import get_db


SECRET_KEY_ENV = "JWT_SECRET_KEY"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


password_hash = PasswordHash.recommended()


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def hash_password(password: str) -> str:

    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str
) -> bool:

    try:
        return password_hash.verify(password, hashed_password)
    except UnknownHashError:
        return False


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    token_version: int = 0,
):

    secret_key = os.getenv(SECRET_KEY_ENV, "")
    if len(secret_key) < 32:
        raise RuntimeError(f"{SECRET_KEY_ENV} must contain at least 32 characters")

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "token_version": token_version,
        "exp": expire
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=ALGORITHM
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:
        secret_key = os.getenv(SECRET_KEY_ENV, "")
        if len(secret_key) < 32:
            raise credentials_exception

        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, ValueError):

        raise credentials_exception

    user = (
        db.query(models.User)
        .filter(
            models.User.id == user_id
        )
        .first()
    )

    if user is None:
        raise credentials_exception

    if (
        not user.is_active
        or payload.get("role") != user.role
        or payload.get("token_version") != user.token_version
    ):
        raise credentials_exception

    return user


def require_student(
    current_user=Depends(get_current_user)
):

    if current_user.role != "student":

        raise HTTPException(
            status_code=403,
            detail="Student access required"
        )

    return current_user


def require_instructor(
    current_user=Depends(get_current_user)
):

    if current_user.role != "instructor":

        raise HTTPException(
            status_code=403,
            detail="Instructor access required"
        )

    return current_user