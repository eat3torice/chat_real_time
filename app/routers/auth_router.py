from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.auth.hashing import hash_password, verify_password, needs_rehash
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user
from app.schemas.auth_schema import UserCreate, UserLogin, UserOut, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user. Hash password then store.
    """
    # check username/email uniqueness
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    if user_in.email:
        existing_email = db.query(User).filter(User.email == user_in.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, username=user.username, email=user.email)


@router.post("/token", response_model=Token)
def login_token(user_login: UserLogin, db: Session = Depends(get_db)) -> Any:
    """
    Login endpoint for token. Accepts JSON body:
      { "username": "<username_or_email>", "password": "<password>" }
    Returns JWT access token on success.
    """
    username = user_login.username
    password = user_login.password

    user = (
        db.query(User)
        .filter((User.username == username) | (User.email == username))
        .first()
    )
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # If hash policy changed, re-hash and update DB transparently
    try:
        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
            db.add(user)
            db.commit()
    except Exception:
        # best-effort: don't prevent login if rehash fails
        pass

    token_payload: Dict[str, Any] = {"id": user.id, "username": user.username}
    access_token = create_access_token(token_payload)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current user information.
    """
    return UserOut(
        id=current_user.id, username=current_user.username, email=current_user.email
    )


@router.post("/login", response_model=Token)
def login(user_login: UserLogin, db: Session = Depends(get_db)) -> Any:
    """
    Login endpoint. Accepts JSON body:
      { "username": "<username_or_email>", "password": "<password>" }
    Returns JWT access token on success.
    """
    print(f"Received login request: username={user_login.username}")
    username = user_login.username
    password = user_login.password

    user = (
        db.query(User)
        .filter((User.username == username) | (User.email == username))
        .first()
    )
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # If hash policy changed, re-hash and update DB transparently
    try:
        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
            db.add(user)
            db.commit()
    except Exception:
        # best-effort: don't prevent login if rehash fails
        pass

    token_payload: Dict[str, Any] = {"id": user.id, "username": user.username}
    access_token = create_access_token(token_payload)
    return Token(access_token=access_token)
