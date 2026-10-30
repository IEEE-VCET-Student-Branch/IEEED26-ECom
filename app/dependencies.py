from fastapi import Header, HTTPException
from .utils.idempotency import MAX_IDEMPOTENCY_KEY_LENGTH, normalize_key


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    key = normalize_key(idempotency_key or "")
    if not key or len(key) > MAX_IDEMPOTENCY_KEY_LENGTH:
        raise HTTPException(400, "Idempotency-Key header is required")
    return key


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()
