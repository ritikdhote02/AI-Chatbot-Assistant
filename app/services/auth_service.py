import hashlib
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.config import get_auth_settings
from app.database import get_connection

password_hasher = PasswordHash.recommended()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def register_user(name: str, email: str, password: str) -> tuple[str, str]:
    user_id = str(uuid4())
    normalized_email = email.strip().lower()
    password_hash = password_hasher.hash(password)

    try:
        with closing(get_connection()) as connection, connection:
            connection.execute(
                """
                INSERT INTO users (id, name, email, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, name.strip(), normalized_email, password_hash),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("An account with this email already exists.") from exc

    token = create_verification_token(user_id)
    return user_id, token


def create_verification_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    expires_at = (utc_now() + timedelta(minutes=30)).isoformat()

    with closing(get_connection()) as connection, connection:
        connection.execute(
            """
            DELETE FROM email_verification_tokens
            WHERE user_id = ?
            """,
            (user_id,),
        )

        connection.execute(
            """
            INSERT INTO email_verification_tokens
                (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
            """,
            (user_id, token_hash, expires_at),
        )

    return token


def verify_email_token(token: str) -> bool:
    token_hash = hash_token(token)
    now = utc_now().isoformat()

    with closing(get_connection()) as connection, connection:
        row = connection.execute(
            """
            SELECT user_id, expires_at
            FROM email_verification_tokens
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

        if row is None:
            return False

        # Consume the token whether expired or valid.
        connection.execute(
            """
            DELETE FROM email_verification_tokens
            WHERE token_hash = ?
            """,
            (token_hash,),
        )

        if row["expires_at"] <= now:
            return False

        connection.execute(
            """
            UPDATE users
            SET is_email_verified = 1
            WHERE id = ?
            """,
            (row["user_id"],),
        )

    return True


def get_user_by_email(email: str):
    with closing(get_connection()) as connection:
        return connection.execute(
            """
            SELECT id, name, email, password_hash, is_email_verified
            FROM users
            WHERE email = ?
            """,
            (email.strip().lower(),),
        ).fetchone()


def get_user_by_id(user_id: str):
    with closing(get_connection()) as connection:
        return connection.execute(
            """
            SELECT id, name, email, is_email_verified
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()


def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)

    # Use a generic error so login doesn't reveal which emails exist.
    if user is None:
        return None, "invalid_credentials"

    if not password_hasher.verify(password, user["password_hash"]):
        return None, "invalid_credentials"

    if not user["is_email_verified"]:
        return None, "email_not_verified"

    return user, None


def create_access_token(user_id: str) -> tuple[str, int]:
    settings = get_auth_settings()
    expires_in = settings["access_token_minutes"] * 60
    now = utc_now()

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings["jwt_secret"],
        algorithm=settings["jwt_algorithm"],
    )

    return token, expires_in
