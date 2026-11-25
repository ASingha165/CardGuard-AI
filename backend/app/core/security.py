"""Security utilities: PAN protection, CSV validation, and API authentication."""
import hashlib
import hmac
import re
import secrets
from typing import Optional, Tuple

from fastapi import Header, HTTPException, status

from app.core.config import get_settings

RAW_PAN_REGEX = re.compile(r"^\d{13,19}$")
RAW_PAN_COLUMN_NAMES = {"card_number", "pan", "cc_num", "credit_card", "card_no", "account_number"}


def mask_and_tokenize_card(raw_or_token: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Never store raw card numbers.
    If given a raw PAN (13-19 digits), returns (hmac_token, last4).
    If already tokenized, normalizes token and extracts last4 safely.
    """
    cleaned = re.sub(r"[\s-]", "", str(raw_or_token or "").strip())
    secret = (salt or get_settings().API_KEY_SECRET).encode("utf-8")

    if RAW_PAN_REGEX.match(cleaned):
        digest = hmac.new(secret, cleaned.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        return f"tok_{digest}", cleaned[-4:]

    if cleaned.startswith("tok_"):
        last4 = cleaned[-4:] if len(cleaned) >= 4 else "0000"
        return cleaned[:24], last4

    digest = hmac.new(secret, cleaned.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    digits = re.findall(r"\d", cleaned)
    last4 = "".join(digits[-4:]) if len(digits) >= 4 else "0000"
    return f"tok_{digest}", last4


def contains_raw_pan(value: str) -> bool:
    cleaned = re.sub(r"[\s-]", "", str(value or "").strip())
    return bool(RAW_PAN_REGEX.match(cleaned))


def validate_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None),
) -> str:
    """
    Authentication boundary for protected endpoints.
    When REQUIRE_AUTH is true, requires valid X-API-Key or Bearer token.
    In local development (REQUIRE_AUTH=false), validates key if supplied and
    otherwise returns 'dev-analyst'.
    """
    settings = get_settings()
    token = x_api_key
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if not settings.REQUIRE_AUTH:
        if token and not secrets.compare_digest(token, settings.API_KEY_SECRET):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API credentials",
            )
        return "analyst"

    if not token or not secrets.compare_digest(token, settings.API_KEY_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: provide valid X-API-Key or Bearer token",
        )
    return "analyst"
