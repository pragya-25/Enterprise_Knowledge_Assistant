"""Password hashing and JWT handling. Uses only the standard library + PyJWT."""
import hashlib
import hmac
import os
import secrets
import time

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.users import get_user_by_username

load_dotenv()

ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
_bearer = HTTPBearer(auto_error=False)


def _secret() -> str:
    s = os.getenv("JWT_SECRET", "")
    if len(s) < 16:
        raise RuntimeError(
            "JWT_SECRET is missing or too short. Generate one with:\n"
            '  python -c "import secrets; print(secrets.token_hex(32))"\n'
            "and add JWT_SECRET=<value> to your .env file.")
    return s


# ---------- passwords (PBKDF2-SHA256, salted) ----------

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


# ---------- tokens ----------

def create_token(username: str, role: str) -> str:
    payload = {"sub": username, "role": role, "exp": int(time.time()) + EXPIRE_MINUTES * 60}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    """The caller's identity and role come from the verified token + database,
    never from anything the client sends in the request body."""
    if creds is None:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, _secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    user = get_user_by_username(payload.get("sub", ""))
    if not user:
        raise HTTPException(401, "User no longer exists")
    return user


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin access required")
    return user
