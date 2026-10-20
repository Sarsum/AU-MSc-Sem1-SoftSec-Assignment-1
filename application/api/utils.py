import bcrypt
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timezone, timedelta
import jwt
import os
from secrets import token_hex
from typing import Any, Literal

def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pw_bytes, salt)
    return hashed_password.decode("utf-8")

DUMMY_HASH = hash_password(token_hex(16))

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))

JWT_PRIVATE_KEY = b""
JWT_PUBLIC_KEY = b""

def load_keys():
    global JWT_PRIVATE_KEY, JWT_PUBLIC_KEY
    try:
        with open(os.getenv("JWT_PRIVKEY_FILE", "../../private.pem"), "rb") as f:
            JWT_PRIVATE_KEY = f.read()
            serialization.load_pem_private_key(JWT_PRIVATE_KEY, password=None)
        with open(os.getenv("JWT_PUBKEY_FILE", "../../public.pem"), "rb") as f:
            JWT_PUBLIC_KEY = f.read()
            serialization.load_pem_public_key(JWT_PUBLIC_KEY)

        print("PEM keys loaded successfully")
    except FileNotFoundError:
        print("CRITICAL: PEM files are missing")
        raise
    except ValueError as e:
        print(f"CRITICAL: PEM format is invalid. Error: {e}")
        raise

def create_token(type: Literal["user", "system"], user_id: int, user_role: str, payload: dict[str, Any]) -> str:
    payload["type"] = type
    payload["user_id"] = user_id
    payload["user_role"] = user_role
    # expiry of 24 hours for user tokens, 10 minutes for system tokens
    if type == "user":
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(hours=24)
    else:
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(minutes=10)
        # avoid duplicate tokens when all values are similar
        payload["id"] = token_hex(16)
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm="EdDSA")

def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=["EdDSA"])
    except:
        return None