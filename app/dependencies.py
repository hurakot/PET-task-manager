
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status

from sqlmodel import select

import jwt
from jwt.exceptions import InvalidTokenError 

from typing import Annotated

from app.database import SessionDep
from app.models import User

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exc
    except InvalidTokenError:
        raise credentials_exc
    result = await session.exec(select(User).where(User.username == username))
    user = result.first()
    if user is None:
        raise credentials_exc
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
