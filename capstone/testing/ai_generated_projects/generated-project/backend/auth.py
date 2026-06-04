from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

"""
This is a stub/mock implementation for demonstration.
Replace with a real authentication & authorization system in production!
"""

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    is_admin: bool


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # DEMO ONLY: decode token, get user
    # In production, validate the JWT, load user from DB, check expiration, etc
    if token == "admin-token":
        return User(username="admin", is_admin=True)
    elif token == "user-token":
        return User(username="user", is_admin=False)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )