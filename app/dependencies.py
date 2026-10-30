from fastapi import Header, HTTPException


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    if not idempotency_key or len(idempotency_key.strip()) > 120 or not idempotency_key.strip():
        raise HTTPException(400, "Idempotency-Key header is required")
    return idempotency_key.strip()


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()
