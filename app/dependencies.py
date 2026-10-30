from fastapi import Header, HTTPException
from .utils.idempotency import normalize_key


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    if not idempotency_key or len(idempotency_key) > 120:
        raise HTTPException(400, "Idempotency-Key header is required")
    return normalize_key(idempotency_key)


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()
