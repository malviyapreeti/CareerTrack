
import os
import json
import base64
import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import get_connection


SECRET_KEY = os.getenv(
    "CAREERTRACK_SECRET_KEY",
    "careertrack-development-secret-change-before-deployment"
)

security = HTTPBearer(auto_error=False)


def encode_part(data):
    encoded = base64.urlsafe_b64encode(
        json.dumps(data, separators=(",", ":")).encode()
    )
    return encoded.decode().rstrip("=")


def decode_part(data):
    padding = "=" * (-len(data) % 4)
    decoded = base64.urlsafe_b64decode(data + padding)
    return json.loads(decoded.decode())


def create_access_token(user_id):
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }

    payload = {
        "sub": str(user_id),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }

    message = encode_part(header) + "." + encode_part(payload)

    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()

    encoded_signature = base64.urlsafe_b64encode(
        signature
    ).decode().rstrip("=")

    return message + "." + encoded_signature


def verify_access_token(token):
    try:
        parts = token.split(".")

        if len(parts) != 3:
            return None

        header = decode_part(parts[0])

        if header.get("alg") != "HS256":
            return None

        message = parts[0] + "." + parts[1]

        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()

        padding = "=" * (-len(parts[2]) % 4)

        actual_signature = base64.urlsafe_b64decode(
            parts[2] + padding
        )

        if not hmac.compare_digest(
            expected_signature,
            actual_signature
        ):
            return None

        payload = decode_part(parts[1])

        if int(payload.get("exp", 0)) <= int(time.time()):
            return None

        return int(payload["sub"])

    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def hash_password(password):
    salt = secrets.token_hex(16)

    hashed_password = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        600000
    )

    return salt + ":" + hashed_password.hex()


def verify_password(password, stored_password):
    try:
        salt, old_hash = stored_password.split(":")

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            600000
        )

        return secrets.compare_digest(
            new_hash.hex(),
            old_hash
        )

    except (ValueError, AttributeError):
        return False


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please login first!"
        )

    user_id = verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token!"
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found!"
            )

        return dict(user)

    finally:
        conn.close()
