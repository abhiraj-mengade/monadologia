"""
auth.py — Authentication Layer

Minimal but secure. API key + JWT. No OAuth. No complex flows.
Because the only thing more boring than bad auth is over-engineered auth.
"""

from __future__ import annotations
import jwt
import time
from typing import Optional
from fastapi import HTTPException, Header

SECRET_KEY = "the-monad-has-no-escape-function-leibniz-was-right"
ALGORITHM = "HS256"
TOKEN_EXPIRY = 86400  # 24 hours


def create_token(agent_id: str, agent_name: str) -> str:
    """Create a JWT for an authenticated agent."""
    payload = {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRY,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_agent_id_from_token(authorization: str = Header(None)) -> str:
    """FastAPI dependency — extract agent_id from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload["agent_id"]
