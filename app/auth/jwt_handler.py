import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from jose import jwt, JWTError

# load secret from env (.env)
SECRET_KEY = os.getenv("SECRET_KEY", "skibidy_sigma_king")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def create_access_token(subject: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT token. subject should include at least {'id': <user_id>}.
    We include iat and exp claims.
    """
    to_encode = subject.copy()
    now = datetime.utcnow()
    to_encode.update({"iat": now})
    if expires_delta is None:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + expires_delta
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify token; raise JWTError on failure.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload