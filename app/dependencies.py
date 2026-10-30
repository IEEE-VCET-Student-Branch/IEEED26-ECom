from fastapi import Header, HTTPException


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    if not idempotency_key or len(idempotency_key) > 120:
        raise HTTPException(400, "Idempotency-Key header is required")
    normalized = idempotency_key.strip().lower()
    if not normalized or len(normalized) > 120:
        raise HTTPException(400, "Idempotency-Key header is required")
    return normalized


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()
