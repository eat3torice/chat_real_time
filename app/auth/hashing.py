import os
import unicodedata
from typing import Optional

from passlib.context import CryptContext

# If you want to tune Argon2 parameters, set these env vars.
ARGON_TIME_COST = int(os.getenv("ARGON_TIME_COST", "2"))
ARGON_MEMORY_COST = int(os.getenv("ARGON_MEMORY_COST", "65536"))  # KiB (64 MiB)
ARGON_PARALLELISM = int(os.getenv("ARGON_PARALLELISM", "1"))

# Use Argon2 as primary scheme. Keep bcrypt_sha256 as fallback if you had older hashes.
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt_sha256"],
    deprecated="auto",
    argon2__time_cost=ARGON_TIME_COST,
    argon2__memory_cost=ARGON_MEMORY_COST,
    argon2__parallelism=ARGON_PARALLELISM,
    bcrypt__rounds=int(os.getenv("BCRYPT_ROUNDS", "12")),
)


def _normalize_password(pw: Optional[str]) -> Optional[str]:
    """
    Normalize unicode to NFC so inputs are consistent.
    Preserve case and internal whitespace.
    """
    if pw is None:
        return None
    return unicodedata.normalize("NFC", pw)


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2 (via passlib).
    """
    norm = _normalize_password(password)
    return pwd_context.hash(norm)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against stored hash. Return False on error.
    """
    norm = _normalize_password(plain_password)
    try:
        return pwd_context.verify(norm, hashed_password)
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Return True when an existing hash should be re-hashed according to current policy.
    """
    try:
        return pwd_context.needs_update(hashed_password)
    except Exception:
        return True
