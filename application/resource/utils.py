from cryptography.hazmat.primitives import serialization
from datetime import datetime, timezone, timedelta
import jwt
import os
from secrets import token_hex
from typing import Any, Literal

JWT_PUBLIC_KEY = b""

def load_keys():
    global JWT_PUBLIC_KEY
    try:
        with open(os.getenv("JWT_PUBKEY_FILE", "../../public.pem"), "rb") as f:
            JWT_PUBLIC_KEY = f.read()
            serialization.load_pem_public_key(JWT_PUBLIC_KEY)

        print("PEM key loaded successfully")
    except FileNotFoundError:
        print("CRITICAL: PEM file is missing")
        raise
    except ValueError as e:
        print(f"CRITICAL: PEM format is invalid. Error: {e}")
        raise

def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=["EdDSA"])
    except:
        return None