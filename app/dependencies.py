from fastapi import Header, HTTPException
from .utils.idempotency import normalize_key


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    if idempotency_key is None:
        raise HTTPException(400, "Idempotency-Key header is required")
    canonical_key = normalize_key(idempotency_key)
    if not canonical_key or len(canonical_key) > 120:
        raise HTTPException(400, "Idempotency-Key header is required")
    return canonical_key


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()
