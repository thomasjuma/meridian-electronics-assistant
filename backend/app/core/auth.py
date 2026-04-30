import os

import jwt
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException, status

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _get_secret_key() -> str:
    """Return the JWT secret key from the environment variable."""
    return os.environ["AUTH_JWT_SECRET_KEY"]


def create_access_token(username: str) -> str:
    """Create a JWT access token for the given username.

    The token includes a 'sub' claim set to the username and an 'exp' claim
    set to now + ACCESS_TOKEN_EXPIRE_MINUTES.

    Args:
        username: The username to encode in the token's 'sub' claim.

    Returns:
        A signed JWT string using HS256.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Decode and validate a JWT access token, returning the username.

    Raises HTTPException(401) for expired or invalid tokens with appropriate
    error messages and WWW-Authenticate headers.

    Args:
        token: The JWT string to decode.

    Returns:
        The username from the token's 'sub' claim.

    Raises:
        HTTPException: 401 if the token is expired or invalid.
    """
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(authorization: str | None = Header(default=None)):
    """Extract and validate Bearer token. Returns username."""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    prefix, _, token = authorization.partition(" ")
    if prefix.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(token)
