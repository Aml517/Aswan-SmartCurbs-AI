import base64
import hashlib
import hmac
import json
import re
import secrets
import binascii
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest

PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    digest = base64.urlsafe_b64encode(derived_key).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        parts = password_hash.split("$")
        if len(parts) != 4:
            return False
        algorithm, iteration_text, salt, expected_digest = parts
        if algorithm != "pbkdf2_sha256":
            return False
        if iteration_text != str(PBKDF2_ITERATIONS):
            return False
        iterations = int(iteration_text)
        if iterations != PBKDF2_ITERATIONS:
            return False
        if re.fullmatch(r"[0-9a-f]{32}", salt) is None:
            return False
        if re.fullmatch(r"[A-Za-z0-9_-]{43}", expected_digest) is None:
            return False
        derived_key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        actual_digest = base64.urlsafe_b64encode(derived_key).decode("ascii").rstrip("=")
        return hmac.compare_digest(actual_digest, expected_digest)
    except (ValueError, TypeError, OverflowError):
        return False


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    if (
        not isinstance(value, str)
        or not value
        or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None
        or len(value) % 4 == 1
    ):
        raise ValueError("Invalid Base64URL")
    padding = "=" * (-len(value) % 4)
    try:
        decoded = base64.b64decode(
            (value + padding).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, UnicodeEncodeError, ValueError):
        raise ValueError("Invalid Base64URL")
    if _base64url_encode(decoded) != value:
        raise ValueError("Invalid Base64URL")
    return decoded


def create_access_token(user_id: int, role: str) -> str:
    if settings.AUTH_ALGORITHM != "HS256":
        raise RuntimeError("Only HS256 authentication tokens are supported")
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    header = {"alg": settings.AUTH_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    encoded_header = _base64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    encoded_payload = _base64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{encoded_header}.{encoded_payload}.{_base64url_encode(signature)}"


def decode_access_token(token: str) -> dict:
    try:
        if not isinstance(token, str):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        segments = token.split(".")
        if len(segments) != 3:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        header_segment, payload_segment, signature_segment = segments
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        supplied_signature = _base64url_decode(signature_segment)
        if len(supplied_signature) != hashlib.sha256().digest_size:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        expected_signature = hmac.new(
            settings.AUTH_SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        header = json.loads(_base64url_decode(header_segment).decode("utf-8"))
        if not isinstance(header, dict):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        if header.get("alg") != settings.AUTH_ALGORITHM:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        if header.get("typ") != "JWT":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
        if not isinstance(payload, dict):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        expires_at = payload.get("exp")
        user_id = payload.get("sub")
        role = payload.get("role")
        issued_at = payload.get("iat")
        if (
            type(expires_at) is not int
            or type(issued_at) is not int
            or expires_at is None
            or issued_at is None
            or not isinstance(user_id, str)
            or re.fullmatch(r"[1-9][0-9]*", user_id) is None
            or role not in ("driver", "admin")
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        now_timestamp = datetime.now(timezone.utc).timestamp()
        if issued_at > now_timestamp:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token issued in the future")
        if expires_at <= issued_at:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        if now_timestamp >= expires_at:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        return {"sub": int(user_id), "role": role}
    except HTTPException:
        raise
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def authenticate_user(data: LoginRequest, db: Session) -> Optional[User]:
    normalized_email = data.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not user.is_active:
        return None
    if not verify_password(data.password, user.password_hash):
        return None
    return user
