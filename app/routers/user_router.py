from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.dependencies import get_current_user
from app.database.models import User
from app.schemas.user_schema import UserOut, UserProfileUpdate, UserPasswordUpdate
from app.auth.hashing import hash_password, verify_password

router = APIRouter()


@router.get("/users/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile information"""
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
    )


@router.put("/users/me", response_model=UserOut)
def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update current user profile (username, email)"""
    try:
        # Check if username already exists (if changed)
        if profile_data.username and profile_data.username != current_user.username:
            existing_user = (
                db.query(User)
                .filter(
                    User.username == profile_data.username, User.id != current_user.id
                )
                .first()
            )
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")
            current_user.username = profile_data.username

        # Check if email already exists (if changed)
        if profile_data.email and profile_data.email != current_user.email:
            existing_user = (
                db.query(User)
                .filter(User.email == profile_data.email, User.id != current_user.id)
                .first()
            )
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already exists")
            current_user.email = profile_data.email

        db.commit()
        db.refresh(current_user)

        return UserOut(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            created_at=current_user.created_at,
        )

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.put("/users/me/password")
def update_user_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Update current user password"""
    try:
        # Verify current password
        if not verify_password(
            password_data.current_password, current_user.password_hash
        ):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Update password
        current_user.password_hash = hash_password(password_data.new_password)
        db.commit()

        return {"status": "success", "message": "Password updated successfully"}

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to update password")
