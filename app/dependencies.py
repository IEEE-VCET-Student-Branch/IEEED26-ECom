from fastapi import Header, HTTPException


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(400, "Idempotency-Key header is required")
    key = idempotency_key.strip()
    if len(key) > 120:
        raise HTTPException(400, "Idempotency-Key header is required")
    return key


def validate_customer_id(customer_id: str) -> str:
    cleaned = customer_id.strip()
    if not cleaned:
        raise HTTPException(400, "Customer ID cannot be blank")
    return cleaned
