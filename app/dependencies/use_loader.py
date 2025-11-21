from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.auth.dependencies import get_current_user_token


def get_user_by_token(
    payload: dict = Depends(get_current_user_token), db: Session = Depends(get_db)
) -> User:
    """
    Given validated token payload (contains 'id'), load full SQLAlchemy User model.
    Raises 401 if not found.
    """
    user_id = payload.get("id")
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user
